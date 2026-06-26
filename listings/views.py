import re

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.utils import OperationalError, ProgrammingError
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ContactForm, InquiryForm, PropertyForm, SignUpForm
from .models import ContactMessage, Favorite, Property


def _is_seller(user):
    return user.is_authenticated and user.groups.filter(name="seller").exists()


def home(request):
    selected_type = request.GET.get("type", "all")
    search_query = request.GET.get("search", "").strip()
    min_price = request.GET.get("min_price", "").strip()
    max_price = request.GET.get("max_price", "").strip()
    city_query = request.GET.get("city", "").strip()
    state_query = request.GET.get("state", "").strip()
    selected_sort = request.GET.get("sort", "newest").strip() or "newest"
    text_search = search_query
    subtitle = "Browse all listed properties without logging in"
    total_results = 0
    page_obj = None

    if search_query:
        range_match = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)", search_query)
        if range_match:
            min_price = min_price or range_match.group(1)
            max_price = max_price or range_match.group(2)
            text_search = text_search.replace(range_match.group(0), " ")

        min_match = re.search(r"\bmin\s*:\s*(\d+(?:\.\d+)?)", search_query, re.IGNORECASE)
        if min_match:
            min_price = min_price or min_match.group(1)
            text_search = text_search.replace(min_match.group(0), " ")

        max_match = re.search(r"\bmax\s*:\s*(\d+(?:\.\d+)?)", search_query, re.IGNORECASE)
        if max_match:
            max_price = max_price or max_match.group(1)
            text_search = text_search.replace(max_match.group(0), " ")

        text_search = " ".join(text_search.split())

    try:
        properties = Property.objects.select_related("owner").filter(sold=False)

        if selected_type in {"rent", "sale"}:
            properties = properties.filter(listing_type=selected_type)
            subtitle = (
                "Browse rental properties without logging in"
                if selected_type == "rent"
                else "Browse properties for sale without logging in"
            )
        else:
            selected_type = "all"

        if text_search:
            properties = properties.filter(
                Q(title__icontains=text_search)
                | Q(city__icontains=text_search)
                | Q(state__icontains=text_search)
                | Q(address__icontains=text_search)
                | Q(zip_code__icontains=text_search)
                | Q(description__icontains=text_search)
            )
            subtitle = f'Search results for "{text_search}"'

        if city_query:
            properties = properties.filter(city__icontains=city_query)
            subtitle = f"Homes in {city_query}" if not text_search else f'{subtitle} · {city_query}'

        if state_query:
            properties = properties.filter(state__icontains=state_query)
            subtitle = f"Homes in {state_query}" if not text_search and not city_query else f'{subtitle} · {state_query}'

        if min_price:
            try:
                properties = properties.filter(price__gte=min_price)
                subtitle = (
                    f"Properties from Ksh {float(min_price):,.0f} and above"
                    if not text_search and not city_query and not state_query
                    else f'{subtitle} · from ${float(min_price):,.0f}'
                )
            except ValueError:
                min_price = ""

        if max_price:
            try:
                properties = properties.filter(price__lte=max_price)
                if min_price:
                    subtitle = (
                        f"Properties from Ksh {float(min_price):,.0f} to Ksh {float(max_price):,.0f}"
                        if not text_search and not city_query and not state_query
                        else f'{subtitle} · up to ${float(max_price):,.0f}'
                    )
                else:
                    subtitle = (
                        f"Properties up to Ksh {float(max_price):,.0f}"
                        if not text_search and not city_query and not state_query
                        else f'{subtitle} · up to ${float(max_price):,.0f}'
                    )
            except ValueError:
                max_price = ""

        sort_options = {
            "newest": ["-listed_date"],
            "oldest": ["listed_date"],
            "price_asc": ["price", "-listed_date"],
            "price_desc": ["-price", "-listed_date"],
            "title_asc": ["title"],
        }
        if selected_sort not in sort_options:
            selected_sort = "newest"
        properties = properties.order_by(*sort_options[selected_sort])

        paginator = Paginator(properties, 8)
        page_obj = paginator.get_page(request.GET.get("page") or 1)
        total_results = paginator.count

        featured_listings = [
            {
                "id": listing.id,
                "title": listing.title,
                "price": f"Ksh {listing.price:,.2f}",
                "listing_type": listing.get_listing_type_display(),
                "location": f"{listing.city}, {listing.state}",
                "address": listing.address,
                "description": listing.description,
                "image_url": listing.image.url if listing.image else None,
                "brochure_url": listing.brochure.url if listing.brochure else None,
                "sold": listing.sold,
            }
            for listing in page_obj.object_list
        ]
    except (OperationalError, ProgrammingError):
        featured_listings = []
        selected_type = "all"
        search_query = ""
        city_query = ""
        state_query = ""
        min_price = ""
        max_price = ""
        selected_sort = "newest"

    query_params = request.GET.copy()
    query_params.pop("page", None)

    context = {
        "title": "PropertyIQ",
        "subtitle": subtitle,
        "featured_listings": featured_listings,
        "selected_type": selected_type,
        "search_query": search_query,
        "min_price": min_price,
        "max_price": max_price,
        "city_query": city_query,
        "state_query": state_query,
        "selected_sort": selected_sort,
        "page_obj": page_obj,
        "total_results": total_results,
        "querystring": query_params.urlencode(),
    }
    return render(request, "listings/home.html", context)


def auth_view(request):
    """Unified authentication view handling both login and signup."""
    mode = request.GET.get("mode", "login")  # "login" or "signup"
    role = request.GET.get("role", "buyer")  # "buyer" or "seller"
    
    if mode == "signup":
        signup_form = SignUpForm(request.POST or None)
        login_form = None
        
        if request.method == "POST" and signup_form.is_valid():
            user = signup_form.save()
            group, _ = Group.objects.get_or_create(name=role)
            user.groups.add(group)
            login(request, user)
            return redirect("dashboard")
        
        form = signup_form
    else:
        login_form = AuthenticationForm(request, data=request.POST or None)
        signup_form = None
        
        if request.method == "POST" and login_form.is_valid():
            login(request, login_form.get_user())
            return redirect("dashboard")
        
        form = login_form
    
    return render(
        request,
        "listings/auth.html",
        {
            "form": form,
            "mode": mode,
            "role": role,
            "login_form": login_form,
            "signup_form": signup_form,
        },
    )


def login_view(request):
    """Legacy view - redirects to unified auth."""
    return auth_view(request)


def register_buyer(request):
    """Legacy view - redirects to unified auth."""
    return auth_view(request)


def register_seller(request):
    """Legacy view - redirects to unified auth."""
    return auth_view(request)


def contact_view(request):
    form = ContactForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Thanks for contacting PropertyIQ. Our team will get back to you soon.")
        return redirect("contact")

    return render(
        request,
        "listings/contact.html",
        {
            "page_title": "Contact Us",
            "subtitle": "We're here to help buyers, sellers, and agents with PropertyIQ.",
            "form": form,
        },
    )


@login_required
def dashboard(request):
    is_seller = _is_seller(request.user)
    role_label = "Agent / Seller" if is_seller else "Buyer"
    owned_properties = (
        Property.objects.filter(owner=request.user).prefetch_related("inquiries").order_by("-listed_date")
        if is_seller
        else []
    )
    saved_properties = (
        Favorite.objects.filter(user=request.user).select_related("property", "property__owner")
        if not is_seller
        else []
    )

    return render(
        request,
        "listings/dashboard.html",
        {
            "role_label": role_label,
            "is_seller": is_seller,
            "owned_properties": owned_properties,
            "saved_properties": saved_properties,
        },
    )


@login_required
def property_create(request):
    if not _is_seller(request.user):
        return HttpResponseForbidden("Only agents/sellers can add properties.")

    form = PropertyForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        property_item = form.save(commit=False)
        property_item.owner = request.user
        property_item.save()
        messages.success(request, "Property added successfully.")
        return redirect("dashboard")

    return render(
        request,
        "listings/property_form.html",
        {"form": form, "page_title": "Add Property", "button_label": "Save Property"},
    )


@login_required
def property_update(request, property_id):
    if not _is_seller(request.user):
        return HttpResponseForbidden("Only agents/sellers can edit properties.")

    property_item = get_object_or_404(Property, id=property_id, owner=request.user)
    form = PropertyForm(request.POST or None, request.FILES or None, instance=property_item)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Property updated successfully.")
        return redirect("dashboard")

    return render(
        request,
        "listings/property_form.html",
        {"form": form, "page_title": "Edit Property", "button_label": "Update Property"},
    )


@login_required
def property_delete(request, property_id):
    if not _is_seller(request.user):
        return HttpResponseForbidden("Only agents/sellers can delete properties.")

    property_item = get_object_or_404(Property, id=property_id, owner=request.user)
    if request.method == "POST":
        property_title = property_item.title
        if property_item.image:
            property_item.image.delete(save=False)
        if property_item.brochure:
            property_item.brochure.delete(save=False)
        property_item.delete()
        messages.success(request, f'"{property_title}" was deleted successfully.')
        return redirect("dashboard")

    return render(request, "listings/property_confirm_delete.html", {"property": property_item})


def property_detail(request, property_id):
    property_item = get_object_or_404(Property.objects.select_related("owner"), id=property_id)
    can_view_inquiries = request.user.is_authenticated and request.user == property_item.owner
    recent_inquiries = property_item.inquiries.select_related("buyer")[:5] if can_view_inquiries else []
    is_favorited = (
        request.user.is_authenticated
        and request.user != property_item.owner
        and Favorite.objects.filter(property=property_item, user=request.user).exists()
    )
    seller_listing_count = Property.objects.filter(owner=property_item.owner).count()

    return render(
        request,
        "listings/property_detail.html",
        {
            "property": property_item,
            "inquiry_form": InquiryForm(),
            "recent_inquiries": recent_inquiries,
            "can_view_inquiries": can_view_inquiries,
            "is_favorited": is_favorited,
            "seller_listing_count": seller_listing_count,
        },
    )


@login_required
def property_inquiry(request, property_id):
    property_item = get_object_or_404(Property.objects.select_related("owner"), id=property_id)

    if request.method != "POST":
        return redirect("property_detail", property_id=property_item.id)

    if request.user == property_item.owner:
        messages.error(request, "You cannot send an inquiry on your own listing.")
        return redirect("property_detail", property_id=property_item.id)

    if property_item.sold:
        messages.error(request, "This property is already sold. Inquiries are closed.")
        return redirect("property_detail", property_id=property_item.id)

    form = InquiryForm(request.POST)
    if form.is_valid():
        inquiry = form.save(commit=False)
        inquiry.property = property_item
        inquiry.buyer = request.user
        inquiry.name = request.user.get_full_name() or request.user.username
        inquiry.email = request.user.email
        inquiry.save()
        messages.success(request, "Inquiry sent successfully.")
        return redirect("property_detail", property_id=property_item.id)

    can_view_inquiries = request.user == property_item.owner
    recent_inquiries = property_item.inquiries.select_related("buyer")[:5] if can_view_inquiries else []
    is_favorited = request.user != property_item.owner and Favorite.objects.filter(
        property=property_item, user=request.user
    ).exists()
    seller_listing_count = Property.objects.filter(owner=property_item.owner).count()
    return render(
        request,
        "listings/property_detail.html",
        {
            "property": property_item,
            "inquiry_form": form,
            "recent_inquiries": recent_inquiries,
            "can_view_inquiries": can_view_inquiries,
            "is_favorited": is_favorited,
            "seller_listing_count": seller_listing_count,
        },
        status=400,
    )


@login_required
def toggle_sold(request, property_id):
    if not _is_seller(request.user):
        return HttpResponseForbidden("Only agents/sellers can update sale status.")

    property_item = get_object_or_404(Property, id=property_id, owner=request.user)

    if request.method != "POST":
        return redirect("dashboard")

    property_item.sold = not property_item.sold
    property_item.save()

    if property_item.sold:
        messages.success(request, f'"{property_item.title}" is now marked as sold.')
    else:
        messages.success(request, f'"{property_item.title}" is now marked as available.')

    return redirect("dashboard")


@login_required
def toggle_favorite(request, property_id):
    property_item = get_object_or_404(Property.objects.select_related("owner"), id=property_id)

    if request.method != "POST":
        return redirect("property_detail", property_id=property_item.id)

    if request.user == property_item.owner:
        messages.error(request, "You cannot save your own listing.")
        return redirect("property_detail", property_id=property_item.id)

    favorite, created = Favorite.objects.get_or_create(property=property_item, user=request.user)
    if created:
        messages.success(request, "Saved to favorites.")
    else:
        favorite.delete()
        messages.success(request, "Removed from favorites.")

    return redirect("property_detail", property_id=property_item.id)


def logout_view(request):
    logout(request)
    return redirect("home")

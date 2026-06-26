import tempfile

from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import ContactMessage, Favorite, Inquiry, Property

TEST_MEDIA_ROOT = tempfile.mkdtemp()


class HomePageTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner1", password="StrongPass123!")
        Property.objects.create(
            listing_type="rent",
            title="Rental Loft",
            description="City rental",
            price="1800.00",
            address="1 Market St",
            city="Seattle",
            state="WA",
            zip_code="98101",
            owner=self.owner,
        )
        Property.objects.create(
            listing_type="sale",
            title="Family Villa",
            description="Home for sale",
            price="650000.00",
            address="99 Palm Rd",
            city="Orlando",
            state="FL",
            zip_code="32801",
            owner=self.owner,
        )

    def test_home_page_loads(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "listings/home.html")
        self.assertContains(response, "PropertyIQ")

    def test_home_page_can_filter_rentals(self):
        response = self.client.get(reverse("home"), {"type": "rent"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rental Loft")
        self.assertNotContains(response, "Family Villa")
        self.assertContains(response, "For Rent")

    def test_home_page_can_filter_sales(self):
        response = self.client.get(reverse("home"), {"type": "sale"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Family Villa")
        self.assertNotContains(response, "Rental Loft")
        self.assertContains(response, "For Sale")

    def test_home_page_displays_each_property_as_card(self):
        Property.objects.create(
            listing_type="rent",
            title="Compact Studio",
            description="Perfect for city living",
            price="1400.00",
            address="321 City Lane",
            city="San Francisco",
            state="CA",
            zip_code="94103",
            owner=self.owner,
        )

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "property-card")
        self.assertContains(response, "Rental Loft")
        self.assertContains(response, "Family Villa")
        self.assertContains(response, "Compact Studio")

    def test_guest_can_view_all_listed_properties_without_login(self):
        for index in range(3, 9):
            Property.objects.create(
                listing_type="sale" if index % 2 == 0 else "rent",
                title=f"Extra Property {index}",
                description="Extra listing",
                price="250000.00",
                address=f"{index} Test Ave",
                city="Phoenix",
                state="AZ",
                zip_code="85001",
                owner=self.owner,
            )

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rental Loft")
        self.assertContains(response, "Family Villa")
        self.assertContains(response, "Extra Property 8")

    def test_home_page_can_search_by_title(self):
        response = self.client.get(reverse("home"), {"search": "Villa"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Family Villa")
        self.assertNotContains(response, "Rental Loft")

    def test_home_page_can_search_by_city(self):
        response = self.client.get(reverse("home"), {"search": "Seattle"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rental Loft")
        self.assertNotContains(response, "Family Villa")

    def test_home_page_can_filter_by_min_price(self):
        response = self.client.get(reverse("home"), {"min_price": "200000"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Family Villa")
        self.assertNotContains(response, "Rental Loft")

    def test_home_page_can_filter_by_max_price(self):
        response = self.client.get(reverse("home"), {"max_price": "2000"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rental Loft")
        self.assertNotContains(response, "Family Villa")

    def test_home_page_uses_single_search_bar(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="search"')
        self.assertNotContains(response, 'name="min_price"')
        self.assertNotContains(response, 'name="max_price"')

    def test_home_page_can_search_by_price_in_single_bar(self):
        response = self.client.get(reverse("home"), {"search": "max:2000"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rental Loft")
        self.assertNotContains(response, "Family Villa")

    def test_home_page_supports_city_filter_and_sorting(self):
        Property.objects.create(
            listing_type="sale",
            title="Seattle Condo",
            description="Modern downtown condo",
            price="710000.00",
            address="88 Pine St",
            city="Seattle",
            state="WA",
            zip_code="98109",
            owner=self.owner,
        )

        response = self.client.get(reverse("home"), {"city": "Seattle", "sort": "price_desc"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Seattle Condo")
        self.assertContains(response, "Rental Loft")
        self.assertNotContains(response, "Family Villa")
        self.assertEqual(response.context["selected_sort"], "price_desc")

    def test_home_page_paginates_large_property_results(self):
        for index in range(3, 11):
            Property.objects.create(
                listing_type="sale",
                title=f"Paged Property {index}",
                description="Paginated listing",
                price="300000.00",
                address=f"{index} Main St",
                city="Miami",
                state="FL",
                zip_code="33101",
                owner=self.owner,
            )

        first_page = self.client.get(reverse("home"))
        second_page = self.client.get(reverse("home"), {"page": 2})

        self.assertEqual(first_page.status_code, 200)
        self.assertEqual(second_page.status_code, 200)
        self.assertContains(first_page, "Paged Property 10")
        self.assertNotContains(first_page, "Rental Loft")
        self.assertContains(second_page, "Rental Loft")
        self.assertTrue(first_page.context["page_obj"].has_next())
        self.assertEqual(second_page.context["page_obj"].number, 2)


class PropertyDetailAndInquiryTests(TestCase):
    def setUp(self):
        self.seller_group, _ = Group.objects.get_or_create(name="seller")
        self.buyer_group, _ = Group.objects.get_or_create(name="buyer")

        self.seller = User.objects.create_user(
            username="agent_detail",
            email="agent@example.com",
            password="StrongPass123!",
        )
        self.seller.groups.add(self.seller_group)

        self.buyer = User.objects.create_user(
            username="buyer_detail",
            email="buyer@example.com",
            password="StrongPass123!",
        )
        self.buyer.groups.add(self.buyer_group)

        self.property = Property.objects.create(
            listing_type="sale",
            title="Modern Townhome",
            description="Close to downtown and transit",
            price="410000.00",
            address="500 Cedar Ave",
            city="Portland",
            state="OR",
            zip_code="97201",
            owner=self.seller,
        )

    def test_property_detail_page_loads(self):
        response = self.client.get(reverse("property_detail", args=[self.property.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Modern Townhome")
        self.assertContains(response, "Portland")
        self.assertContains(response, "Contact Agent")

    def test_property_detail_shows_agent_profile_card(self):
        response = self.client.get(reverse("property_detail", args=[self.property.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Agent Profile")
        self.assertContains(response, "agent@example.com")
        self.assertContains(response, "Response time")

    def test_buyer_can_submit_property_inquiry(self):
        self.client.login(username="buyer_detail", password="StrongPass123!")

        response = self.client.post(
            reverse("property_inquiry", args=[self.property.id]),
            {
                "phone": "555-123-4567",
                "message": "I would like to schedule a viewing this week.",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Inquiry.objects.filter(property=self.property, buyer=self.buyer, phone="555-123-4567").exists()
        )
        self.assertContains(response, "Inquiry sent successfully")

    def test_guest_must_log_in_to_send_inquiry(self):
        response = self.client.post(
            reverse("property_inquiry", args=[self.property.id]),
            {
                "phone": "555-987-6543",
                "message": "Please contact me.",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_buyer_can_save_property_to_favorites(self):
        self.client.login(username="buyer_detail", password="StrongPass123!")

        response = self.client.post(reverse("toggle_favorite", args=[self.property.id]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Favorite.objects.filter(property=self.property, user=self.buyer).exists())
        self.assertContains(response, "Saved to favorites")

    def test_buyer_can_remove_property_from_favorites(self):
        Favorite.objects.create(property=self.property, user=self.buyer)
        self.client.login(username="buyer_detail", password="StrongPass123!")

        response = self.client.post(reverse("toggle_favorite", args=[self.property.id]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Favorite.objects.filter(property=self.property, user=self.buyer).exists())
        self.assertContains(response, "Removed from favorites")


class AuthenticationTests(TestCase):
    def test_login_page_loads(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Login")

    def test_login_page_shows_shared_navbar_links(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "All Listings")
        self.assertContains(response, "Rentals")
        self.assertContains(response, "For Sale")
        self.assertContains(response, "Contact Us")
        self.assertContains(response, "Sign Up")
        self.assertContains(response, "Agent / Seller Sign Up")
        self.assertContains(response, "Buyer Sign Up")

    def test_contact_page_loads(self):
        response = self.client.get(reverse("contact"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "listings/contact.html")
        self.assertContains(response, "Contact Us")
        self.assertContains(response, "support@propertyiq.com")

    def test_contact_form_submission_saves_message(self):
        response = self.client.post(
            reverse("contact"),
            {
                "name": "Taylor Buyer",
                "email": "taylor@example.com",
                "subject": "Need help with a listing",
                "message": "I'm interested in a home and need more details.",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(ContactMessage.objects.filter(email="taylor@example.com").exists())
        self.assertContains(response, "Thanks for contacting PropertyIQ")

    def test_buyer_signup_creates_user_and_logs_in(self):
        response = self.client.post(
            reverse("register_buyer"),
            {
                "username": "buyer1",
                "email": "buyer@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
            follow=True,
        )

        self.assertTrue(User.objects.filter(username="buyer1").exists())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Buyer")

    def test_seller_signup_creates_user_and_logs_in(self):
        response = self.client.post(
            reverse("register_seller"),
            {
                "username": "seller1",
                "email": "seller@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
            follow=True,
        )

        self.assertTrue(User.objects.filter(username="seller1").exists())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Agent / Seller")


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class PropertyManagementTests(TestCase):
    def setUp(self):
        self.seller_group, _ = Group.objects.get_or_create(name="seller")
        self.buyer_group, _ = Group.objects.get_or_create(name="buyer")

        self.seller = User.objects.create_user(username="agent1", password="StrongPass123!")
        self.seller.groups.add(self.seller_group)

        self.buyer = User.objects.create_user(username="buyer2", password="StrongPass123!")
        self.buyer.groups.add(self.buyer_group)

    def test_seller_can_add_property(self):
        self.client.login(username="agent1", password="StrongPass123!")

        response = self.client.post(
            reverse("property_create"),
            {
                "listing_type": "rent",
                "title": "Lake House",
                "description": "Spacious home near the lake",
                "price": "450000.00",
                "address": "12 Lake Road",
                "city": "Austin",
                "state": "TX",
                "zip_code": "78701",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Property.objects.filter(title="Lake House", owner=self.seller, listing_type="rent").exists())
        self.assertContains(response, "Lake House")

    def test_buyer_cannot_add_property(self):
        self.client.login(username="buyer2", password="StrongPass123!")

        response = self.client.get(reverse("property_create"))

        self.assertEqual(response.status_code, 403)

    def test_seller_can_upload_image_and_pdf(self):
        self.client.login(username="agent1", password="StrongPass123!")
        image = SimpleUploadedFile("home.jpg", b"fake-image-content", content_type="image/jpeg")
        brochure = SimpleUploadedFile("brochure.pdf", b"%PDF-1.4 fake pdf", content_type="application/pdf")

        response = self.client.post(
            reverse("property_create"),
            {
                "listing_type": "sale",
                "title": "Upload House",
                "description": "Listing with files",
                "price": "500000.00",
                "address": "25 River St",
                "city": "Boston",
                "state": "MA",
                "zip_code": "02110",
                "image": image,
                "brochure": brochure,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        property_item = Property.objects.get(title="Upload House")
        self.assertTrue(property_item.image.name.endswith("home.jpg"))
        self.assertTrue(property_item.brochure.name.endswith("brochure.pdf"))

    def test_seller_can_update_property(self):
        property_item = Property.objects.create(
            listing_type="sale",
            title="Old Title",
            description="Needs updates",
            price="320000.00",
            address="44 Hill St",
            city="Denver",
            state="CO",
            zip_code="80014",
            owner=self.seller,
        )
        self.client.login(username="agent1", password="StrongPass123!")

        response = self.client.post(
            reverse("property_update", args=[property_item.id]),
            {
                "listing_type": "rent",
                "title": "Updated Title",
                "description": "Renovated property",
                "price": "350000.00",
                "address": "44 Hill St",
                "city": "Denver",
                "state": "CO",
                "zip_code": "80014",
            },
            follow=True,
        )

        property_item.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(property_item.title, "Updated Title")
        self.assertEqual(property_item.listing_type, "rent")

    def test_seller_can_delete_property(self):
        property_item = Property.objects.create(
            listing_type="sale",
            title="Delete Me",
            description="Temporary listing",
            price="120000.00",
            address="10 Pine Ave",
            city="Dallas",
            state="TX",
            zip_code="75001",
            owner=self.seller,
        )
        self.client.login(username="agent1", password="StrongPass123!")

        response = self.client.post(reverse("property_delete", args=[property_item.id]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Property.objects.filter(id=property_item.id).exists())

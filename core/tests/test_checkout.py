from django.test import TestCase, Client
from django.urls import reverse

class CheckoutPageTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_checkout_page_loads(self):
        response = self.client.get(reverse('checkout'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'checkout.html')

from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from website.models import ContactMessage, Service
from website.utils.ip import get_client_ip, is_valid_ip
from django.contrib.auth.models import User

class ClientIPUtilityTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_is_valid_ip(self):
        self.assertTrue(is_valid_ip('192.168.1.1'))
        self.assertTrue(is_valid_ip('127.0.0.1'))
        self.assertTrue(is_valid_ip('203.0.113.195'))
        self.assertTrue(is_valid_ip('2001:0db8:85a3:0000:0000:8a2e:0370:7334'))
        self.assertTrue(is_valid_ip('::1'))
        self.assertFalse(is_valid_ip('invalid-ip'))
        self.assertFalse(is_valid_ip('999.999.999.999'))
        self.assertFalse(is_valid_ip(''))
        self.assertFalse(is_valid_ip(None))
        self.assertFalse(is_valid_ip(12345))

    def test_remote_addr_ipv4(self):
        request = self.factory.get('/', REMOTE_ADDR='203.0.113.10')
        self.assertEqual(get_client_ip(request), '203.0.113.10')

    def test_remote_addr_ipv6(self):
        request = self.factory.get('/', REMOTE_ADDR='2001:db8::1')
        self.assertEqual(get_client_ip(request), '2001:db8::1')

    def test_cloudflare_connecting_ip_precedence(self):
        request = self.factory.get(
            '/',
            REMOTE_ADDR='127.0.0.1',
            HTTP_CF_CONNECTING_IP='198.51.100.42'
        )
        self.assertEqual(get_client_ip(request), '198.51.100.42')

    def test_x_forwarded_for_first_client_ip(self):
        request = self.factory.get(
            '/',
            REMOTE_ADDR='127.0.0.1',
            HTTP_X_FORWARDED_FOR='203.0.113.50, 10.0.0.1, 192.168.1.1'
        )
        self.assertEqual(get_client_ip(request), '203.0.113.50')

    def test_invalid_header_falls_back_safely(self):
        request = self.factory.get(
            '/',
            REMOTE_ADDR='203.0.113.10',
            HTTP_CF_CONNECTING_IP='bad-ip-string',
            HTTP_X_FORWARDED_FOR='another-bad-string'
        )
        # Bypasses the invalid CF/X-Forwarded headers and falls back to valid REMOTE_ADDR
        self.assertEqual(get_client_ip(request), '203.0.113.10')

    def test_empty_or_none_request(self):
        self.assertIsNone(get_client_ip(None))
        request = self.factory.get('/')
        # When neither valid IP is present
        request.META['REMOTE_ADDR'] = ''
        self.assertIsNone(get_client_ip(request))


class LeadFormIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser('admin_test', 'admin@example.com', 'testpass123')

    def test_thank_you_page_renders_properly(self):
        """Verify the /thank-you/ page returns 200 and has expected elements."""
        response = self.client.get(reverse('thank_you'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Thank You")
        self.assertContains(response, "Your enquiry has been received")
        self.assertContains(response, "Back to Home")

    def test_contact_page_form_successful_submission_with_ip(self):
        """Verify submission from Contact page creates a lead with IP and redirects to /thank-you/."""
        payload = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone': '+1234567890',
            'subject': 'Inquiry about SEO',
            'message': 'Hello, I want to discuss a project.'
        }
        response = self.client.post(reverse('contact'), payload, REMOTE_ADDR='198.51.100.25')
        self.assertRedirects(response, reverse('thank_you'))
        
        lead = ContactMessage.objects.filter(email='john@example.com').first()
        self.assertIsNotNone(lead)
        self.assertEqual(lead.name, 'John Doe')
        self.assertEqual(lead.phone, '+1234567890')
        self.assertEqual(lead.subject, 'Inquiry about SEO')
        self.assertEqual(lead.ip_address, '198.51.100.25')

    def test_home_page_form_successful_submission_with_ipv6(self):
        """Verify submission using Home Page lead form payload captures IPv6 address."""
        payload = {
            'name': 'Alice Smith',
            'email': 'alice@example.com',
            'phone': '9876543210',
            'subject': 'Home Page Lead',
            'message': 'Need AI consulting for enterprise.'
        }
        response = self.client.post(reverse('contact'), payload, REMOTE_ADDR='2001:db8:85a3::8a2e:370:7334')
        self.assertRedirects(response, reverse('thank_you'))
        
        lead = ContactMessage.objects.filter(email='alice@example.com').first()
        self.assertIsNotNone(lead)
        self.assertEqual(lead.name, 'Alice Smith')
        self.assertEqual(lead.subject, 'Home Page Lead')
        self.assertEqual(lead.ip_address, '2001:db8:85a3::8a2e:370:7334')

    def test_cloudflare_forwarded_ip_submission(self):
        """Verify submission behind Cloudflare captures the CF-Connecting-IP."""
        payload = {
            'name': 'Cloudflare Visitor',
            'email': 'cf@example.com',
            'phone': '1234567890',
            'subject': 'Cloudflare Inquiry',
            'message': 'Testing CF IP preservation'
        }
        response = self.client.post(
            reverse('contact'),
            payload,
            REMOTE_ADDR='127.0.0.1',
            HTTP_CF_CONNECTING_IP='203.0.113.88'
        )
        self.assertRedirects(response, reverse('thank_you'))
        lead = ContactMessage.objects.filter(email='cf@example.com').first()
        self.assertIsNotNone(lead)
        self.assertEqual(lead.ip_address, '203.0.113.88')

    def test_service_page_form_successful_submission(self):
        """Verify submission from dynamic service page creates a lead and captures IP."""
        service = Service.objects.create(
            title='AI Strategy Consulting',
            slug='ai-strategy-consulting',
            status='PUBLISHED',
            content='<p>Sample service content</p>'
        )
        payload = {
            'name': 'Bob Consultant',
            'email': 'bob@consulting.com',
            'phone': '5551234567',
            'subject': f'Service Inquiry: {service.title}',
            'message': 'Interested in AI consulting services.'
        }
        # Post to contact
        response = self.client.post(reverse('contact'), payload, REMOTE_ADDR='198.51.100.12')
        self.assertRedirects(response, reverse('thank_you'))

        lead = ContactMessage.objects.filter(email='bob@consulting.com').first()
        self.assertIsNotNone(lead)
        self.assertEqual(lead.name, 'Bob Consultant')
        self.assertEqual(lead.subject, 'Service Inquiry: AI Strategy Consulting')
        self.assertEqual(lead.ip_address, '198.51.100.12')

        # Also test direct POST to dynamic service detail route
        payload2 = {
            'name': 'Charlie Partner',
            'email': 'charlie@partner.com',
            'phone': '5559876543',
            'subject': f'Service Inquiry: {service.title}',
            'message': 'Looking for a partnership.'
        }
        response2 = self.client.post(f'/{service.slug}/', payload2, REMOTE_ADDR='198.51.100.15')
        self.assertRedirects(response2, reverse('thank_you'))
        lead2 = ContactMessage.objects.filter(email='charlie@partner.com').first()
        self.assertIsNotNone(lead2)
        self.assertEqual(lead2.ip_address, '198.51.100.15')

    def test_form_validation_failure_does_not_redirect_to_thank_you(self):
        """Verify invalid submission does NOT create lead and does NOT redirect to /thank-you/."""
        initial_count = ContactMessage.objects.count()
        payload = {
            'name': '', # Missing required name
            'email': 'not-an-email', # Invalid email
            'phone': '',
            'message': ''
        }
        response = self.client.post(reverse('contact'), payload)
        self.assertEqual(response.status_code, 200) # Re-rendered page with errors
        self.assertEqual(ContactMessage.objects.count(), initial_count)

    def test_dashboard_displays_submitted_leads_with_ip(self):
        """Verify submitted lead shows up in dashboard lead list with IP address."""
        lead = ContactMessage.objects.create(
            name='Dashboard Test Lead',
            email='lead@test.com',
            phone='1112223333',
            subject='Dashboard Test Subject',
            message='Test inquiry body',
            ip_address='203.0.113.99'
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard_lead_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard Test Lead')
        self.assertContains(response, 'lead@test.com')
        self.assertContains(response, 'Dashboard Test Subject')
        self.assertContains(response, '203.0.113.99')

        # Also check lead detail page
        detail_response = self.client.get(reverse('dashboard_lead_detail', kwargs={'pk': lead.pk}))
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, '203.0.113.99')

    def test_dashboard_legacy_lead_without_ip_renders_safely(self):
        """Verify older records with NULL ip_address display cleanly without crashing."""
        legacy_lead = ContactMessage.objects.create(
            name='Legacy Lead',
            email='legacy@test.com',
            phone='9998887777',
            subject='Old Lead Prior to IP Tracking',
            message='Legacy inquiry without IP address',
            ip_address=None
        )
        self.client.force_login(self.user)
        
        # Test in list view
        list_response = self.client.get(reverse('dashboard_lead_list'))
        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, 'Legacy Lead')

        # Test in detail view
        detail_response = self.client.get(reverse('dashboard_lead_detail', kwargs={'pk': legacy_lead.pk}))
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, 'Not recorded')

    def test_dashboard_search_by_ip(self):
        """Verify filtering dashboard leads by IP address returns matching leads."""
        ContactMessage.objects.create(
            name='Target Lead',
            email='target@test.com',
            phone='1231231234',
            subject='IP Search Target',
            ip_address='198.51.100.77'
        )
        ContactMessage.objects.create(
            name='Other Lead',
            email='other@test.com',
            phone='4564564567',
            subject='Other Subject',
            ip_address='192.0.2.1'
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard_lead_list') + '?q=198.51.100.77')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Target Lead')
        self.assertNotContains(response, 'Other Lead')


from website.models import BlockedIP
from website.utils.spam_check import is_ip_blocked
from django.utils import timezone
from datetime import timedelta
from django.core import mail


class BlockedIPTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser('admin_sec', 'admin_sec@example.com', 'testpass123')

    def test_spam_check_utility_unblocked_ip(self):
        """Unblocked IP should return False."""
        self.assertFalse(is_ip_blocked('198.51.100.88'))
        self.assertFalse(is_ip_blocked(None))
        self.assertFalse(is_ip_blocked('invalid-ip-string'))

    def test_spam_check_utility_blocked_ipv4(self):
        """Active blocked IPv4 should return True and increment blocked_attempts_count."""
        block = BlockedIP.objects.create(
            ip_address='198.51.100.99',
            reason='Known spam bot',
            is_active=True
        )
        self.assertTrue(is_ip_blocked('198.51.100.99'))
        block.refresh_from_db()
        self.assertEqual(block.blocked_attempts_count, 1)
        self.assertIsNotNone(block.last_attempt_at)

    def test_spam_check_utility_blocked_ipv6(self):
        """Active blocked IPv6 should return True."""
        BlockedIP.objects.create(
            ip_address='2001:db8:85a3::8a2e:370:7334',
            reason='IPv6 crawler spam',
            is_active=True
        )
        self.assertTrue(is_ip_blocked('2001:db8:85a3::8a2e:370:7334'))

    def test_spam_check_inactive_or_expired_block(self):
        """Inactive or expired block should return False and not block."""
        # 1. Inactive block
        BlockedIP.objects.create(
            ip_address='198.51.100.101',
            is_active=False
        )
        self.assertFalse(is_ip_blocked('198.51.100.101'))

        # 2. Expired block
        past_time = timezone.now() - timedelta(hours=2)
        BlockedIP.objects.create(
            ip_address='198.51.100.102',
            is_active=True,
            expires_at=past_time
        )
        self.assertFalse(is_ip_blocked('198.51.100.102'))

    def test_contact_form_blocked_submission_prevents_db_and_email(self):
        """Form submission from a blocked IP must not create a lead and must not send emails."""
        BlockedIP.objects.create(
            ip_address='203.0.113.200',
            reason='Blacklisted Spammer',
            is_active=True
        )
        initial_lead_count = ContactMessage.objects.count()
        mail.outbox.clear()

        payload = {
            'name': 'Spammer Name',
            'email': 'spam@badbot.com',
            'phone': '1234567890',
            'subject': 'Buy Cheap Links',
            'message': 'Spam content message here'
        }
        response = self.client.post(reverse('contact'), payload, REMOTE_ADDR='203.0.113.200', follow=True)
        self.assertEqual(response.status_code, 200)

        # Confirm no lead was added to the DB
        self.assertEqual(ContactMessage.objects.count(), initial_lead_count)
        # Confirm no email was dispatched
        self.assertEqual(len(mail.outbox), 0)

        # Confirm attempt counter incremented
        block = BlockedIP.objects.get(ip_address='203.0.113.200')
        self.assertEqual(block.blocked_attempts_count, 1)

    def test_dashboard_blocked_ips_crud(self):
        """Verify staff can access, add, toggle, and delete blocked IPs in dashboard."""
        self.client.force_login(self.user)

        # 1. List view renders
        list_response = self.client.get(reverse('dashboard_blocked_ip_list'))
        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, 'Blocked IP Addresses')

        # 2. Add blocked IP via POST
        create_response = self.client.post(reverse('dashboard_blocked_ip_create'), {
            'ip_address': '198.51.100.55',
            'reason': 'Abusive bot submissions',
            'is_active': 'on'
        }, follow=True)
        self.assertEqual(create_response.status_code, 200)
        self.assertTrue(BlockedIP.objects.filter(ip_address='198.51.100.55').exists())

        # 3. Toggle status
        block = BlockedIP.objects.get(ip_address='198.51.100.55')
        self.assertTrue(block.is_active)
        toggle_response = self.client.post(reverse('dashboard_blocked_ip_toggle', kwargs={'pk': block.pk}), follow=True)
        self.assertEqual(toggle_response.status_code, 200)
        block.refresh_from_db()
        self.assertFalse(block.is_active)

        # 4. Delete block
        delete_response = self.client.post(reverse('dashboard_blocked_ip_delete', kwargs={'pk': block.pk}), follow=True)
        self.assertEqual(delete_response.status_code, 200)
        self.assertFalse(BlockedIP.objects.filter(ip_address='198.51.100.55').exists())

    def test_1_click_block_from_lead_detail(self):
        """Verify staff can block an abusive lead's IP directly from the lead detail screen."""
        lead = ContactMessage.objects.create(
            name='Abusive User',
            email='abuser@example.com',
            phone='1112223333',
            subject='Spam Inquiry',
            ip_address='198.51.100.80'
        )
        self.client.force_login(self.user)

        # Trigger 1-click block
        post_response = self.client.post(reverse('dashboard_lead_block_ip', kwargs={'pk': lead.pk}), follow=True)
        self.assertEqual(post_response.status_code, 200)
        self.assertTrue(BlockedIP.objects.filter(ip_address='198.51.100.80', is_active=True).exists())

        # Viewing lead detail now reflects blocked status
        detail_response = self.client.get(reverse('dashboard_lead_detail', kwargs={'pk': lead.pk}))
        self.assertContains(detail_response, 'Currently Blocked')


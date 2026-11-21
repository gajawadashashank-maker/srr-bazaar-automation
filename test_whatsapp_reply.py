import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Import functions from app
from app import (
    ask_groq_stylist,
    format_whatsapp_reply_with_links,
    send_whatsapp_text,
    handle_whatsapp_customer_reply,
    claim_whatsapp_message,
)

class TestWhatsAppReply(unittest.TestCase):
    def test_groq_stylist_live_or_fallback(self):
        """Test Groq inference with live API key or graceful fallback."""
        query = "Do you have Edu Kondala Nomu for Sankranti pooja?"
        res = ask_groq_stylist(query)
        self.assertIn("reply", res)
        self.assertIn("product_ids", res)
        self.assertIsInstance(res["product_ids"], list)
        self.assertTrue(len(res["reply"]) > 10)
        print(f"\n[TestGroq] Reply preview: {res['reply'][:120]}... | IDs: {res['product_ids']}")

    def test_format_whatsapp_reply_with_links(self):
        """Verify formatted WhatsApp text includes store links and courier details."""
        raw_reply = "Namaste! We have beautiful Edu Kondala Nomu set available with brass diyas."
        formatted = format_whatsapp_reply_with_links(raw_reply, [592133224])
        self.assertIn("srrbazaar.com", formatted)
        self.assertIn("The Professional Couriers", formatted)
        self.assertIn("Armoor Hub", formatted)
        self.assertIn("+91 9948633303", formatted)
        print(f"\n[TestFormat] Formatted text preview:\n{formatted}")

    @patch("requests.post")
    def test_send_whatsapp_text_mock(self, mock_post):
        """Verify send_whatsapp_text constructs correct Meta Cloud API request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"messages": [{"id": "wamid.HBgL...=="}]}
        mock_post.return_value = mock_response

        success = send_whatsapp_text("918185012453", "Hello from SRR Bazaar!")
        self.assertTrue(success)
        self.assertTrue(mock_post.called)
        call_kwargs = mock_post.call_args.kwargs
        self.assertEqual(call_kwargs["json"]["to"], "918185012453")
        self.assertEqual(call_kwargs["json"]["messaging_product"], "whatsapp")
        self.assertEqual(call_kwargs["json"]["text"]["body"], "Hello from SRR Bazaar!")
        print("\n[TestSend] Successfully verified Meta WhatsApp Cloud API call structure.")

    def test_claim_whatsapp_text_message(self):
        """Verify claim_whatsapp_message claims text message and prevents duplicates."""
        import uuid
        msg_id = f"test_msg_{uuid.uuid4().hex[:8]}"
        msg = {
            "id": msg_id,
            "from": "919948633303",
            "type": "text",
            "text": {"body": "Price of 33 Diya Stand?"}
        }
        first_claim = claim_whatsapp_message(msg)
        second_claim = claim_whatsapp_message(msg)
        self.assertTrue(first_claim, "First delivery must be claimed")
        self.assertFalse(second_claim, "Duplicate delivery must be rejected")
        print("\n[TestClaim] Deduplication test passed successfully.")

    @patch("app._verify_meta_signature")
    @patch("app.handle_whatsapp_customer_reply")
    def test_webhook_customer_text_routing(self, mock_reply_handler, mock_verify_sig):
        """Verify receive_whatsapp_webhook properly routes incoming customer text messages."""
        import asyncio
        import json
        from fastapi import BackgroundTasks
        from unittest.mock import AsyncMock
        from app import receive_whatsapp_webhook
        import uuid

        unique_id = f"wamid_test_{uuid.uuid4().hex[:8]}"
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "metadata": {
                                    "phone_number_id": os.getenv("WHATSAPP_PHONE_NUMBER_ID", "dummy")
                                },
                                "messages": [
                                    {
                                        "id": unique_id,
                                        "from": "919948633303",
                                        "type": "text",
                                        "text": {"body": "Where is my order?"}
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        mock_request = MagicMock()
        mock_request.body = AsyncMock(return_value=json.dumps(payload).encode("utf-8"))
        mock_request.headers = {}

        bg_tasks = BackgroundTasks()
        res = asyncio.run(receive_whatsapp_webhook(mock_request, bg_tasks))
        self.assertEqual(res["status"], "received")
        self.assertEqual(res["queued_tasks"], 1)
        self.assertEqual(len(bg_tasks.tasks), 1)
        # Execute background task
        for task in bg_tasks.tasks:
            task.func(*task.args, **task.kwargs)
        self.assertTrue(mock_reply_handler.called)
        print("\n[TestWebhook] Customer incoming text webhook dispatched and executed AI reply handler successfully.")

if __name__ == "__main__":
    unittest.main()

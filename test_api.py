
import asyncio
import aiohttp
import time
from typing import Dict, Any, Optional

class BindSyncTester:
    def __init__(self, base_url: str = "http://localhost:8000", api_token: str = None):
        self.base_url = base_url
        self.session = None
        self.api_token = api_token
        self.admin_session_token = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_health_check(self) -> Dict[str, Any]:
        print("🔍 Testing health check endpoint...")
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Health check successful!")
                    print(f"   Status: {data.get('status')}")
                    print(f"   Version: {data.get('version')}")
                    runtime = data.get('runtime', {})
                    print(f"   Runtime:")
                    print(f"      - Telegram Bot: {'✅' if runtime.get('telegram_bot') else '❌'}")
                    print(f"      - Discord Bot: {'✅' if runtime.get('discord_bot') else '❌'}")
                    print(f"      - Slack Bot: {'✅' if runtime.get('slack_bot') else '❌'}")
                    print(f"      - API Configured: {'✅' if runtime.get('api_configured') else '❌'}")
                    return data
                else:
                    print(f"❌ Health check failed with status: {response.status}")
                    text = await response.text()
                    print(f"   Response: {text}")
                    return {"error": f"HTTP {response.status}", "response": text}
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return {"error": str(e)}

    async def test_get_messages(self, limit: int = 10, offset: int = 0) -> Dict[str, Any]:

        print(f"📖 Testing get messages (limit={limit}, offset={offset})...")
        headers = {}
        if self.api_token:
            headers['X-API-Token'] = self.api_token
        try:
            async with self.session.get(f"{self.base_url}/messages?limit={limit}&offset={offset}", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    message_count = len(data.get('messages', []))
                    print(f"✅ Retrieved {message_count} messages successfully!")
                    return data
                else:
                    print(f"❌ Get messages failed with status: {response.status}")
                    text = await response.text()
                    print(f"   Response: {text}")
                    return {"error": f"HTTP {response.status}", "response": text}
        except Exception as e:
            print(f"❌ Get messages error: {e}")
            return {"error": str(e)}

    async def test_send_message(self, username: str = "TestUser", text: str = "Hello from test script!", reply_to_id: Optional[str] = None) -> Dict[str, Any]:
        print(f"📤 Testing send message (user: {username}, text: '{text[:30]}...')...")

        payload = {
            "username": username,
            "text": text
        }

        if reply_to_id is not None:
            payload["reply_to_id"] = reply_to_id

        headers = {}
        if self.api_token:
            headers['X-API-Token'] = self.api_token

        try:
            async with self.session.post(f"{self.base_url}/messages", json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Message sent successfully!")
                    print(f"   Message ID: {data.get('id')}")
                    print(f"   Telegram ID: {data.get('tg_msg_id')}")
                    print(f"   Slack TS: {data.get('slack_ts')}")
                    print(f"   Discord ID: {data.get('dc_msg_id')}")
                    return data
                else:
                    print(f"❌ Send message failed with status: {response.status}")
                    text = await response.text()
                    print(f"   Response: {text}")
                    return {"error": f"HTTP {response.status}", "response": text}
        except Exception as e:
            print(f"❌ Send message error: {e}")
            return {"error": str(e)}

    async def test_reply_to_message(self, message_id: str, username: str = "TestUser", text: str = "This is a test reply!", target: Optional[str] = None) -> Dict[str, Any]:
        print(f"💬 Testing reply to message {message_id}...")

        payload = {
            "username": username,
            "text": text
        }

        if target:
            payload["target"] = target

        headers = {}
        if self.api_token:
            headers['X-API-Token'] = self.api_token

        try:
            async with self.session.post(f"{self.base_url}/messages/{message_id}/reply", json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Reply sent successfully!")
                    print(f"   Reply ID: {data.get('id')}")
                    print(f"   Slack TS: {data.get('slack_ts')}")
                    print(f"   Telegram ID: {data.get('tg_msg_id')}")
                    print(f"   Discord ID: {data.get('dc_msg_id')}")
                    return data
                else:
                    print(f"❌ Reply failed with status: {response.status}")
                    text = await response.text()
                    print(f"   Response: {text}")
                    return {"error": f"HTTP {response.status}", "response": text}
        except Exception as e:
            print(f"❌ Reply error: {e}")
            return {"error": str(e)}

    async def test_reply_with_mention(self, message_id: str, username: str = "TestUser", mention_user: str = "Alice") -> Dict[str, Any]:
        text = f"@{mention_user} This is a reply with a mention!"
        print(f"💬 Testing reply with mention (@{mention_user})...")
        return await self.test_reply_to_message(message_id, username, text)

    async def test_send_message_with_tags(self, username: str = "TestUser", mentioned_users: list = None) -> Dict[str, Any]:
        if mentioned_users is None:
            mentioned_users = ["Alice", "Bob"]

        mentions = " ".join([f"@{user}" for user in mentioned_users])
        text = f"{mentions} Hello everyone! This is a test message with tags."

        print(f"📤 Testing send message with tags ({mentions})...")
        return await self.test_send_message(username, text)

    async def test_targeted_message(self, username: str = "TestUser", text: str = "Targeted message test", target: str = "telegram") -> Dict[str, Any]:
        print(f"🎯 Testing targeted message (target: {target})...")

        payload = {
            "username": username,
            "text": text,
            "target": target
        }

        headers = {}
        if self.api_token:
            headers['X-API-Token'] = self.api_token

        try:
            async with self.session.post(f"{self.base_url}/messages", json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Targeted message sent successfully!")
                    print(f"   Message ID: {data.get('id')}")
                    print(f"   Target: {target}")
                    return data
                else:
                    print(f"❌ Targeted message failed with status: {response.status}")
                    text = await response.text()
                    print(f"   Response: {text}")
                    return {"error": f"HTTP {response.status}", "response": text}
        except Exception as e:
            print(f"❌ Targeted message error: {e}")
            return {"error": str(e)}

    async def test_get_specific_message(self, message_id: str) -> Dict[str, Any]:
        print(f"🔎 Testing get specific message {message_id}...")
        headers = {}
        if self.api_token:
            headers['X-API-Token'] = self.api_token
        try:
            async with self.session.get(f"{self.base_url}/messages/{message_id}", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Retrieved message successfully!")
                    print(f"   Text: {data.get('text', '')[:50]}...")
                    return data
                elif response.status == 404:
                    print(f"⚠️  Message not found (404)")
                    return {"error": "Message not found"}
                else:
                    print(f"❌ Get message failed with status: {response.status}")
                    text = await response.text()
                    print(f"   Response: {text}")
                    return {"error": f"HTTP {response.status}", "response": text}
        except Exception as e:
            print(f"❌ Get message error: {e}")
            return {"error": str(e)}

    async def test_frontend(self) -> Dict[str, Any]:
        print("🌐 Testing frontend endpoint...")
        try:
            async with self.session.get(f"{self.base_url}/") as response:
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    if 'html' in content_type:
                        print("✅ Frontend HTML served successfully!")
                        return {"status": "success", "content_type": content_type}
                    else:
                        data = await response.json()
                        print(f"✅ Frontend response: {data}")
                        return data
                else:
                    print(f"❌ Frontend failed with status: {response.status}")
                    text = await response.text()
                    print(f"   Response: {text}")
                    return {"error": f"HTTP {response.status}", "response": text}
        except Exception as e:
            print(f"❌ Frontend error: {e}")
            return {"error": str(e)}

    async def test_admin_status(self) -> Dict[str, Any]:
        print("📊 Testing admin status endpoint...")
        try:
            async with self.session.get(f"{self.base_url}/admin/status") as response:
                if response.status == 200:
                    data = await response.json()
                    admin_exists = data.get('admin_exists', False)
                    print(f"✅ Admin status retrieved!")
                    print(f"   Admin exists: {'✅ Yes' if admin_exists else '❌ No (registration required)'}")
                    return data
                else:
                    print(f"❌ Admin status check failed with status: {response.status}")
                    text = await response.text()
                    print(f"   Response: {text}")
                    return {"error": f"HTTP {response.status}", "response": text}
        except Exception as e:
            print(f"❌ Admin status error: {e}")
            return {"error": str(e)}

    async def test_admin_register(self, username: str, password: str) -> Dict[str, Any]:
        print(f"📝 Testing admin registration (username: {username})...")
        payload = {
            "username": username,
            "password": password
        }
        try:
            async with self.session.post(f"{self.base_url}/admin/register", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Admin registered successfully!")
                    print(f"   Username: {data.get('admin', {}).get('username')}")
                    return data
                else:
                    print(f"❌ Admin registration failed with status: {response.status}")
                    text = await response.text()
                    print(f"   Response: {text}")
                    return {"error": f"HTTP {response.status}", "response": text}
        except Exception as e:
            print(f"❌ Admin registration error: {e}")
            return {"error": str(e)}

    async def test_admin_login(self, username: str, password: str) -> Dict[str, Any]:
        print(f"🔐 Testing admin login (username: {username})...")
        payload = {
            "username": username,
            "password": password
        }
        try:
            async with self.session.post(f"{self.base_url}/admin/login", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    self.admin_session_token = data.get('session_token')
                    print(f"✅ Admin login successful!")
                    print(f"   Session token: {self.admin_session_token[:16]}...")
                    return data
                else:
                    print(f"❌ Admin login failed with status: {response.status}")
                    text = await response.text()
                    print(f"   Response: {text}")
                    return {"error": f"HTTP {response.status}", "response": text}
        except Exception as e:
            print(f"❌ Admin login error: {e}")
            return {"error": str(e)}

    async def test_create_api_token(self, name: str, description: str = None, expires_in_days: int = None) -> Dict[str, Any]:
        print(f"🔑 Testing create API token (name: {name})...")
        if not self.admin_session_token:
            print("❌ No admin session token! Login first.")
            return {"error": "Not authenticated"}

        payload = {"name": name}
        if description:
            payload["description"] = description
        if expires_in_days:
            payload["expires_in_days"] = expires_in_days

        headers = {"X-Admin-Token": self.admin_session_token}

        try:
            async with self.session.post(f"{self.base_url}/admin/tokens", json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    token = data.get('token', {}).get('token')
                    print(f"✅ API token created successfully!")
                    print(f"   Token: {token[:16]}...")
                    print(f"   Name: {data.get('token', {}).get('name')}")
                    return data
                else:
                    print(f"❌ Create token failed with status: {response.status}")
                    text = await response.text()
                    print(f"   Response: {text}")
                    return {"error": f"HTTP {response.status}", "response": text}
        except Exception as e:
            print(f"❌ Create token error: {e}")
            return {"error": str(e)}

    async def test_list_api_tokens(self) -> Dict[str, Any]:
        print(f"📋 Testing list API tokens...")
        if not self.admin_session_token:
            print("❌ No admin session token! Login first.")
            return {"error": "Not authenticated"}

        headers = {"X-Admin-Token": self.admin_session_token}

        try:
            async with self.session.get(f"{self.base_url}/admin/tokens", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    token_count = len(data.get('tokens', []))
                    print(f"✅ Retrieved {token_count} tokens!")
                    for token in data.get('tokens', []):
                        status = "✅ Active" if token.get('is_active') else "❌ Revoked"
                        print(f"   - {token.get('name')}: {status}")
                    return data
                else:
                    print(f"❌ List tokens failed with status: {response.status}")
                    text = await response.text()
                    print(f"   Response: {text}")
                    return {"error": f"HTTP {response.status}", "response": text}
        except Exception as e:
            print(f"❌ List tokens error: {e}")
            return {"error": str(e)}

    async def test_revoke_api_token(self, token_name: str) -> Dict[str, Any]:
        print(f"🚫 Testing revoke API token (name: {token_name})...")
        if not self.admin_session_token:
            print("❌ No admin session token! Login first.")
            return {"error": "Not authenticated"}

        headers = {"X-Admin-Token": self.admin_session_token}

        try:
            async with self.session.patch(f"{self.base_url}/admin/tokens/{token_name}/revoke", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Token '{token_name}' revoked successfully!")
                    return data
                else:
                    print(f"❌ Revoke token failed with status: {response.status}")
                    text = await response.text()
                    print(f"   Response: {text}")
                    return {"error": f"HTTP {response.status}", "response": text}
        except Exception as e:
            print(f"❌ Revoke token error: {e}")
            return {"error": str(e)}

    async def test_without_token(self) -> Dict[str, Any]:
        print(f"🔒 Testing API access without token (should fail)...")
        try:
            async with self.session.get(f"{self.base_url}/messages") as response:
                if response.status == 401:
                    print(f"✅ Correctly rejected request without token (401)")
                    return {"status": "success", "message": "Authentication working correctly"}
                else:
                    print(f"❌ Unexpected status: {response.status} (expected 401)")
                    text = await response.text()
                    return {"error": f"Expected 401, got {response.status}", "response": text}
        except Exception as e:
            print(f"❌ Test error: {e}")
            return {"error": str(e)}

async def run_system_check():
    print("=" * 60)
    print("This will verify all system components without requiring tokens")

    async with BindSyncTester() as tester:
        print("1️⃣ Testing health endpoint...")
        health_result = await tester.test_health_check()
        print()

        print("2️⃣ Testing admin status...")
        status_result = await tester.test_admin_status()
        print()

        print("3️⃣ Testing frontend...")
        await tester.test_frontend()
        print()

        print("4️⃣ Testing API protection (without token)...")
        await tester.test_without_token()
        print()

        # Summary
        print("=" * 60)
        print("📊 SYSTEM CHECK SUMMARY")
        print("-" * 60)

        health_ok = health_result.get('status') == 'healthy' if 'error' not in health_result else False
        admin_exists = status_result.get('admin_exists', False) if 'error' not in status_result else False

        print(f"Health Status:        {'✅ HEALTHY' if health_ok else '❌ UNHEALTHY'}")
        print(f"Admin Configured:     {'✅ YES' if admin_exists else '⚠️  NO (registration needed)'}")

        if health_ok:
            runtime = health_result.get('runtime', {})
            print(f"Telegram Bot:         {'✅ RUNNING' if runtime.get('telegram_bot') else '❌ NOT RUNNING'}")
            print(f"Discord Bot:          {'✅ RUNNING' if runtime.get('discord_bot') else '❌ NOT RUNNING'}")
            print(f"Slack Bot:            {'✅ RUNNING' if runtime.get('slack_bot') else '❌ NOT RUNNING'}")
            print(f"Database:             {'✅ CONNECTED' if runtime.get('api_configured') else '❌ DISCONNECTED'}")

        print("=" * 60)

        if not admin_exists:
            print("\n⚠️  NEXT STEPS:")
            print("   1. Register an admin: python test_api.py setup")
            print("   2. Then run full tests: python test_api.py full")

async def run_comprehensive_test():
    print("🚀 Starting BindSync API Comprehensive Test")
    print("=" * 50)
    print("⚠️  NOTE: This test requires an API token!")
    print("    Get a token from: http://localhost:8000/admin")
    print()

    token = input("Enter your API token: ").strip()

    if not token:
        print("❌ Token is required for API testing")
        return

    async with BindSyncTester(api_token=token) as tester:
        print("\n1️⃣ Testing health check...")
        await tester.test_health_check()
        print()

        print("2️⃣ Testing get existing messages...")
        messages_result = await tester.test_get_messages()
        print()

        print("3️⃣ Testing send message...")
        send_result = await tester.test_send_message(
            username="TestScript",
            text=f"Test message sent at {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print()

        if "id" in send_result:
            message_id = send_result["id"]

            print("4️⃣ Testing get specific message...")
            await tester.test_get_specific_message(message_id)
            print()

            print("5️⃣ Testing reply to message...")
            await tester.test_reply_to_message(
                message_id,
                username="TestReply",
                text=f"Reply to test message at {time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            print()

            print("6️⃣ Testing reply with mention...")
            await tester.test_reply_with_mention(
                message_id,
                username="TestReply",
                mention_user="TestScript"
            )
            print()

        print("7️⃣ Testing message with tags...")
        tagged_result = await tester.test_send_message_with_tags(
            username="TagTester",
            mentioned_users=["Alice", "Bob", "Charlie"]
        )
        print()

        print("8️⃣ Testing targeted message (Telegram only)...")
        await tester.test_targeted_message(
            username="TargetTest",
            text="This message should only go to Telegram",
            target="telegram"
        )
        print()

        print("9️⃣ Testing targeted message (Discord only)...")
        await tester.test_targeted_message(
            username="TargetTest",
            text="This message should only go to Discord",
            target="discord"
        )
        print()

        print("🔟 Getting updated message list...")
        await tester.test_get_messages(limit=5)

    print("=" * 50)
    print("✨ Comprehensive test completed!")

async def run_quick_test():
    print("⚡ Quick API Status Test")
    print("=" * 30)
    print("⚠️  NOTE: This test requires an API token!")
    print("    Get a token from: http://localhost:8000/admin")
    print()

    token = input("Enter your API token: ").strip()

    if not token:
        print("❌ Token is required")
        return

    async with BindSyncTester(api_token=token) as tester:
        print("\n📊 Testing API access...")
        messages_result = await tester.test_get_messages(limit=5)

        if "error" not in messages_result:
            print("\n✅ API is accessible and working!")
        else:
            print("\n❌ API access failed")

async def run_message_test():
    print("📤 Message Sending Test")
    print("=" * 25)
    print("⚠️  NOTE: This test requires an API token!")
    print("    Get a token from: http://localhost:8000/admin")
    print()

    token = input("Enter your API token: ").strip()

    if not token:
        print("❌ Token is required to test message sending")
        return

    async with BindSyncTester(api_token=token) as tester:
        result = await tester.test_send_message(
            username="QuickTest",
            text="Quick message test - checking bot connectivity"
        )

        if "error" not in result:
            tg_sent = result.get("tg_msg_id") is not None
            dc_sent = result.get("dc_msg_id") is not None
            slack_sent = result.get("slack_ts") is not None

            print(f"\n📊 Message Delivery Summary:")
            print(f"   Telegram: {'✅ Sent' if tg_sent else '❌ Failed'}")
            print(f"   Discord: {'✅ Sent' if dc_sent else '❌ Failed'}")
            print(f"   Slack: {'✅ Sent' if slack_sent else '❌ Failed'}")

            if not tg_sent and not dc_sent and not slack_sent:
                print("\n⚠️ No messages were sent to any platform!")
                print("   Check the server console output for detailed error messages.")

async def run_setup():
    print("🔧 BindSync Initial Setup")
    print("Let's set up your admin account")
    print()
    async with BindSyncTester() as tester:
        status = await tester.test_admin_status()
        if status.get('admin_exists'):
            print("\n⚠️  Admin already registered!")
            print("   Use 'python test_api.py auth <username> <password>' to test authentication")
            return

        print("\n📝 Register Admin Account")
        username = input("Enter admin username: ").strip()
        password = input("Enter admin password: ").strip()

        if not username or not password:
            print("❌ Username and password are required!")
            return

        result = await tester.test_admin_register(username, password)

        if "error" not in result:
            print("\n✅ Setup complete!")
            print("   You can now:")
            print(f"   1. Login at: http://localhost:8000/admin")
            print(f"   2. Create API tokens for accessing the API")
            print(f"   3. Run tests: python test_api.py auth {username} <password>")

async def run_auth_test(admin_username: str = None, admin_password: str = None):
    print("🔐 Authentication & Token Management Test")
    print("=" * 50)

    if not admin_username or not admin_password:
        print("❌ Please provide admin credentials:")
        print("   python test_api.py auth <username> <password>")
        return

    async with BindSyncTester() as tester:
        print("\n1️⃣ Testing API access without token (should fail)...")
        await tester.test_without_token()
        print()

        print("2️⃣ Testing admin login...")
        login_result = await tester.test_admin_login(admin_username, admin_password)
        if "error" in login_result:
            print("❌ Cannot continue without valid login")
            return
        print()

        print("3️⃣ Testing API token creation...")
        token_result = await tester.test_create_api_token(
            name=f"TestToken_{int(time.time())}",
            description="Automated test token",
            expires_in_days=30
        )

        api_token = None
        if "token" in token_result:
            api_token = token_result["token"].get("token")
        print()

        print("4️⃣ Testing list all tokens...")
        await tester.test_list_api_tokens()
        print()

        if api_token:
            print("5️⃣ Testing API with valid token...")
            tester.api_token = api_token

            messages_result = await tester.test_get_messages(limit=5)
            print()

            if "error" not in messages_result:
                print("6️⃣ Testing send message with token...")
                send_result = await tester.test_send_message(
                    username="TokenTest",
                    text=f"Message sent with API token at {time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
                print()

            token_name = token_result["token"].get("name")
            print(f"7️⃣ Testing token revocation...")
            await tester.test_revoke_api_token(token_name)
            print()

            print("8️⃣ Testing API with revoked token (should fail)...")
            messages_result = await tester.test_get_messages(limit=5)
            if "error" in messages_result:
                print("✅ Revoked token correctly rejected!")
            print()

            print("9️⃣ Final token list...")
            await tester.test_list_api_tokens()

    print("=" * 50)
    print("✅ Authentication test completed!")

async def run_token_based_test(api_token: str):
    print("🔑 API Token-Based Test")
    print("=" * 50)

    async with BindSyncTester(api_token=api_token) as tester:
        print("1️⃣ Testing get messages with token...")
        messages_result = await tester.test_get_messages()
        print()

        print("2️⃣ Testing send message with token...")
        send_result = await tester.test_send_message(
            username="TokenUser",
            text=f"Token-authenticated message at {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print()

        if "id" in send_result:
            message_id = send_result["id"]

            print("3️⃣ Testing get specific message...")
            await tester.test_get_specific_message(message_id)
            print()

            print("4️⃣ Testing reply with token...")
            await tester.test_reply_to_message(
                message_id,
                username="TokenReply",
                text="Reply using API token"
            )
            print()

            print("5️⃣ Testing reply with mention...")
            await tester.test_reply_with_mention(
                message_id,
                username="TokenReply",
                mention_user="TokenUser"
            )

    print("=" * 50)
    print("✅ Token-based test completed!")

async def run_all_endpoints_test():
    print("🎯 Complete Endpoint Testing Suite")
    print("=" * 60)
    print("⚠️  NOTE: This test requires an API token!")
    print("    Get a token from: http://localhost:8000/admin")
    print()

    token = input("Enter your API token: ").strip()

    if not token:
        print("❌ Token is required for API testing")
        return

    async with BindSyncTester(api_token=token) as tester:
        print("\n📊 HEALTH & STATUS CHECKS")
        print("=" * 60)

        print("1️⃣ Testing health endpoint...")
        await tester.test_health_check()
        print()

        print("2️⃣ Testing frontend endpoint...")
        await tester.test_frontend()
        print()

        print("\n📖 MESSAGE RETRIEVAL TESTS")
        print("=" * 60)

        print("3️⃣ Testing get messages (default limit)...")
        messages_result = await tester.test_get_messages()
        print()

        print("4️⃣ Testing get messages (limit=5, offset=0)...")
        await tester.test_get_messages(limit=5, offset=0)
        print()

        print("5️⃣ Testing get messages (limit=3, offset=2)...")
        await tester.test_get_messages(limit=3, offset=2)
        print()

        print("\n📤 MESSAGE SENDING TESTS")
        print("=" * 60)

        print("6️⃣ Testing send simple message...")
        simple_msg = await tester.test_send_message(
            username="EndpointTester",
            text=f"Simple test message at {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print()

        print("7️⃣ Testing send message with tags/mentions...")
        tagged_msg = await tester.test_send_message_with_tags(
            username="MentionTester",
            mentioned_users=["Alice", "Bob", "Charlie"]
        )
        print()

        print("8️⃣ Testing targeted message (Telegram)...")
        tg_msg = await tester.test_targeted_message(
            username="TargetTest",
            text="Telegram-only message",
            target="telegram"
        )
        print()

        print("9️⃣ Testing targeted message (Discord)...")
        dc_msg = await tester.test_targeted_message(
            username="TargetTest",
            text="Discord-only message",
            target="discord"
        )
        print()

        print("🔟 Testing targeted message (Slack)...")
        slack_msg = await tester.test_targeted_message(
            username="TargetTest",
            text="Slack-only message",
            target="slack"
        )
        print()

        print("\n💬 REPLY TESTS")
        print("=" * 60)

        if "id" in simple_msg:
            message_id = simple_msg["id"]

            print("1️⃣1️⃣ Testing get specific message...")
            await tester.test_get_specific_message(message_id)
            print()

            print("1️⃣2️⃣ Testing simple reply...")
            await tester.test_reply_to_message(
                message_id,
                username="ReplyTester",
                text=f"Simple reply at {time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            print()

            print("1️⃣3️⃣ Testing reply with mention...")
            await tester.test_reply_with_mention(
                message_id,
                username="ReplyTester",
                mention_user="EndpointTester"
            )
            print()

            print("1️⃣4️⃣ Testing reply with multiple mentions...")
            multi_mention_reply = await tester.test_reply_to_message(
                message_id,
                username="ReplyTester",
                text="@Alice @Bob @Charlie Check this out!"
            )
            print()

            print("1️⃣5️⃣ Testing targeted reply (Telegram only)...")
            await tester.test_reply_to_message(
                message_id,
                username="ReplyTester",
                text="This reply should only go to Telegram",
                target="telegram"
            )
            print()

            print("1️⃣6️⃣ Testing targeted reply (Discord only)...")
            await tester.test_reply_to_message(
                message_id,
                username="ReplyTester",
                text="This reply should only go to Discord",
                target="discord"
            )
            print()

        print("\n🔍 EDGE CASES & ERROR HANDLING")
        print("=" * 60)

        print("1️⃣7️⃣ Testing get non-existent message...")
        await tester.test_get_specific_message("non_existent_id_12345")
        print()

        print("1️⃣8️⃣ Testing reply to non-existent message...")
        await tester.test_reply_to_message(
            "non_existent_id_12345",
            username="ErrorTester",
            text="This should fail"
        )
        print()

        print("\n📊 FINAL MESSAGE LIST")
        print("=" * 60)

        print("1️⃣9️⃣ Getting final message list (last 10)...")
        await tester.test_get_messages(limit=10)
        print()

        print("=" * 60)
        print("✨ All endpoint tests completed!")
        print("=" * 60)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        if test_type == "system" or test_type == "check":
            asyncio.run(run_system_check())
        elif test_type == "setup":
            asyncio.run(run_setup())
        elif test_type == "quick":
            asyncio.run(run_quick_test())
        elif test_type == "message":
            asyncio.run(run_message_test())
        elif test_type == "auth":
            if len(sys.argv) >= 4:
                username = sys.argv[2]
                password = sys.argv[3]
                asyncio.run(run_auth_test(username, password))
            else:
                print("Usage: python test_api.py auth <username> <password>")
        elif test_type == "token":
            if len(sys.argv) >= 3:
                token = sys.argv[2]
                asyncio.run(run_token_based_test(token))
            else:
                print("Usage: python test_api.py token <your_api_token>")
        elif test_type == "full":
            asyncio.run(run_comprehensive_test())
        elif test_type == "all" or test_type == "endpoints":
            asyncio.run(run_all_endpoints_test())
        elif test_type == "help" or test_type == "--help" or test_type == "-h":
            print("=" * 70)
            print("BindSync API Test Suite")
            print("=" * 70)
            print("\nAvailable commands:")
            print("  system | check                     - System health check (no token needed)")
            print("  setup                              - Initial admin setup")
            print("  quick                              - Quick API status test")
            print("  message                            - Message sending test")
            print("  auth <username> <password>         - Full authentication test")
            print("  token <api_token>                  - Token-based API test")
            print("  full                               - Comprehensive test suite")
            print("  all | endpoints                    - Test ALL endpoints (19 tests)")
            print("  help                               - Show this help message")
            print("\nExamples:")
            print("  python test_api.py system          - Check if everything is running")
            print("  python test_api.py setup           - First time setup")
            print("  python test_api.py auth admin pass - Test with admin credentials")
            print("  python test_api.py all             - Complete endpoint testing")
            print("\nNew Features Tested:")
            print("  ✅ Message replies with mentions/tags")
            print("  ✅ Messages with multiple user mentions")
            print("  ✅ Targeted messages (platform-specific)")
            print("  ✅ Targeted replies (platform-specific)")
            print("  ✅ Edge cases and error handling")
            print("=" * 70)
        else:
            print(f"❌ Unknown command: {test_type}")
            print("Run 'python test_api.py help' for available commands")
    else:
        asyncio.run(run_system_check())

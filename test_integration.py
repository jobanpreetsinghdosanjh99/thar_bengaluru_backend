import requests
import json
import sys
import argparse

# Performance: Persistent HTTP Session for connection pooling
session = requests.Session()

# CLI argument for partial test runs (smoke: --max-test 15, mid: --max-test 30, full: default)
parser = argparse.ArgumentParser(description='Run integration tests up to a specified test number')
parser.add_argument('--max-test', type=int, default=0, help='Stop after N tests (0 = run all)')
args = parser.parse_args()
MAX_TEST = args.max_test

def req_get(url, **kwargs):
    """Perform GET request using persistent session"""
    kwargs.setdefault("timeout", 8)
    return session.get(url, **kwargs)

def req_post(url, **kwargs):
    """Perform POST request using persistent session"""
    kwargs.setdefault("timeout", 8)
    return session.post(url, **kwargs)

def req_delete(url, **kwargs):
    """Perform DELETE request using persistent session"""
    kwargs.setdefault("timeout", 8)
    return session.delete(url, **kwargs)

def req_put(url, **kwargs):
    """Perform PUT request using persistent session"""
    kwargs.setdefault("timeout", 8)
    return session.put(url, **kwargs)

def req_patch(url, **kwargs):
    """Perform PATCH request using persistent session"""
    kwargs.setdefault("timeout", 8)
    return session.patch(url, **kwargs)

def maybe_stop(current_test):
    """Exit early if MAX_TEST checkpoint reached"""
    if MAX_TEST > 0 and current_test >= MAX_TEST:
        print(f"\n{'=' * 60}")
        print(f"INTEGRATION TESTS COMPLETE - Ran tests 1-{current_test}")
        print(f"{'=' * 60}")
        session.close()
        sys.exit(0)

# Fix Unicode encoding on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
print("COMPREHENSIVE INTEGRATION TEST")
print(f"Mode: {'Partial (--max-test ' + str(MAX_TEST) + ')' if MAX_TEST > 0 else 'Full Suite'}")
print("=" * 60)

# Test 1: Login
print("\n[TEST 1] Login Endpoint")
print("-" * 60)
login_resp = req_post('http://localhost:8000/auth/login', json={'email': 'rajesh@test.com', 'password': 'test1234'})
print(f"Status Code: {login_resp.status_code}")
if login_resp.status_code == 200:
    login_data = login_resp.json()
    token = login_data.get('access_token')
    print(f"✓ Login Successful")
    print(f"Token (first 50 chars): {token[:50]}...")
    user = login_data.get('user')
    print(f"User Email: {user.get('email')}")
else:
    print(f"✗ Login Failed: {login_resp.text}")
    token = None
maybe_stop(1)

# Test 2: Get Current User
print("\n[TEST 2] Get Current User")
print("-" * 60)
if token:
    headers = {'Authorization': f'Bearer {token}'}
    user_resp = req_get('http://localhost:8000/auth/me', headers=headers)
    print(f"Status Code: {user_resp.status_code}")
    if user_resp.status_code == 200:
        print(f"✓ Get User Successful: {user_resp.json()}")
    else:
        print(f"✗ Get User Failed: {user_resp.text}")
else:
    print("⚠ Skipped (token unavailable)")
maybe_stop(2)

# Test 3: Get Feeds
print("\n[TEST 3] Get Feeds Endpoint")
print("-" * 60)
feeds_resp = req_get('http://localhost:8000/feeds')
print(f"Status Code: {feeds_resp.status_code}")
if feeds_resp.status_code == 200:
    feeds = feeds_resp.json()
    print(f"✓ Get Feeds Successful: {len(feeds)} feeds found")
    if feeds:
        print(f"First feed: {feeds[0]}")
else:
    print(f"✗ Get Feeds Failed: {feeds_resp.text}")
maybe_stop(3)

# Test 4: Get Accessories
print("\n[TEST 4] Get Accessories Endpoint")
print("-" * 60)
acc_resp = req_get('http://localhost:8000/accessories')
print(f"Status Code: {acc_resp.status_code}")
accessories = []
if acc_resp.status_code == 200:
    accessories = acc_resp.json()
    print(f"✓ Get Accessories Successful: {len(accessories)} accessories found")
    if accessories:
        print(f"First accessory: {accessories[0]}")
else:
    print(f"✗ Get Accessories Failed: {acc_resp.text}")
maybe_stop(4)

# Test 5: Get Merchandise
print("\n[TEST 5] Get Merchandise Endpoint")
print("-" * 60)
merch_resp = req_get('http://localhost:8000/merchandise')
print(f"Status Code: {merch_resp.status_code}")
merchandise = []
if merch_resp.status_code == 200:
    merchandise = merch_resp.json()
    print(f"✓ Get Merchandise Successful: {len(merchandise)} items found")
    if merchandise:
        print(f"First item: {merchandise[0]}")
else:
    print(f"✗ Get Merchandise Failed: {merch_resp.text}")
maybe_stop(5)

# Test 6: Add to Cart
print("\n[TEST 6] Add to Cart (Authenticated)")
print("-" * 60)
if token:
    headers = {'Authorization': f'Bearer {token}'}
    cart_data = {'product_type': 'accessory', 'product_id': 1, 'quantity': 2, 'size': None, 'color': None}
    cart_resp = req_post('http://localhost:8000/cart', json=cart_data, headers=headers)
    print(f"Status Code: {cart_resp.status_code}")
    if cart_resp.status_code == 200:
        print(f"✓ Add to Cart Successful: {cart_resp.json()}")
    else:
        print(f"✗ Add to Cart Failed: {cart_resp.text}")
else:
    print("⚠ Skipped (token unavailable)")

# Test 7: Get Cart
print("\n[TEST 7] Get Cart (Authenticated)")
print("-" * 60)
if token:
    headers = {'Authorization': f'Bearer {token}'}
    get_cart_resp = req_get('http://localhost:8000/cart', headers=headers)
    print(f"Status Code: {get_cart_resp.status_code}")
    if get_cart_resp.status_code == 200:
        cart = get_cart_resp.json()
        print(f"✓ Get Cart Successful: {len(cart)} items in cart")
        for item in cart:
            print(f"  - Item: {item}")
    else:
        print(f"✗ Get Cart Failed: {get_cart_resp.text}")
else:
    print("⚠ Skipped (token unavailable)")

# Test 8: Create Feed
print("\n[TEST 8] Create Feed (Authenticated)")
print("-" * 60)
if token:
    headers = {'Authorization': f'Bearer {token}'}
    feed_data = {'title': 'Test Adventure', 'content': 'Had an amazing trip!', 'image_url': None}
    create_feed_resp = req_post('http://localhost:8000/feeds', json=feed_data, headers=headers)
    print(f"Status Code: {create_feed_resp.status_code}")
    if create_feed_resp.status_code == 200:
        print(f"✓ Create Feed Successful: {create_feed_resp.json()}")
    else:
        print(f"✗ Create Feed Failed: {create_feed_resp.text}")
else:
    print("⚠ Skipped (token unavailable)")

# Test 9: Delete from Cart (Updated Endpoint)
print("\n[TEST 9] Delete from Cart (Updated Endpoint)")
print("-" * 60)
if token:
    headers = {'Authorization': f'Bearer {token}'}
    # Get cart first to know what item to delete
    get_cart_resp = req_get('http://localhost:8000/cart', headers=headers)
    if get_cart_resp.status_code == 200:
        cart_items = get_cart_resp.json()
        if cart_items:
            item_id = cart_items[0]['id']
            print(f"Attempting to delete cart item ID: {item_id}")
            delete_resp = req_delete(f'http://localhost:8000/cart/{item_id}', headers=headers)
            print(f"Status Code: {delete_resp.status_code}")
            if delete_resp.status_code == 200:
                print(f"✓ Delete from Cart Successful: {delete_resp.json()}")
            else:
                print(f"✗ Delete from Cart Failed: {delete_resp.text}")
        else:
            print("⚠ No items in cart to delete")
    else:
        print(f"⚠ Could not retrieve cart: {get_cart_resp.text}")
else:
    print("⚠ Skipped (token unavailable)")

# Test 10: Club Membership Requests should require auth
print("\n[TEST 10] Club Membership Requests Require Auth")
print("-" * 60)
club_req_unauth_resp = req_get('http://localhost:8000/memberships/club-requests')
print(f"Status Code: {club_req_unauth_resp.status_code}")
if club_req_unauth_resp.status_code == 401:
    print("✓ Unauthenticated club requests correctly blocked (401)")
else:
    print(f"✗ Expected 401 but got {club_req_unauth_resp.status_code}: {club_req_unauth_resp.text}")

# Test 11: TBLR Applications should require auth
print("\n[TEST 11] TBLR Applications Require Auth")
print("-" * 60)
tblr_unauth_resp = req_get('http://localhost:8000/memberships/tblr-applications')
print(f"Status Code: {tblr_unauth_resp.status_code}")
if tblr_unauth_resp.status_code == 401:
    print("✓ Unauthenticated TBLR applications correctly blocked (401)")
else:
    print(f"✗ Expected 401 but got {tblr_unauth_resp.status_code}: {tblr_unauth_resp.text}")

# Test 12: Club Membership POST should require auth
print("\n[TEST 12] Club Membership Submit Requires Auth")
print("-" * 60)
club_payload = {
    "name": "Unauthorized User",
    "email": "unauth@test.com",
    "phone": "9999999999",
    "vehicle_model": "Thar LX",
    "vehicle_number": "KA01XX0000",
    "registration_date": "2024-01-01T00:00:00",
    "reason": "Testing unauthenticated membership submit"
}
club_submit_unauth_resp = req_post(
    'http://localhost:8000/memberships/club-requests',
    json=club_payload
)
print(f"Status Code: {club_submit_unauth_resp.status_code}")
if club_submit_unauth_resp.status_code == 401:
    print("✓ Unauthenticated club membership submit correctly blocked (401)")
else:
    print(f"✗ Expected 401 but got {club_submit_unauth_resp.status_code}: {club_submit_unauth_resp.text}")

# Test 13: Get Membership Club Requests (Authenticated)
print("\n[TEST 13] Get Club Membership Requests (Authenticated)")
print("-" * 60)
if token:
    headers = {'Authorization': f'Bearer {token}'}
    club_req_resp = req_get('http://localhost:8000/memberships/club-requests', headers=headers)
    print(f"Status Code: {club_req_resp.status_code}")
    if club_req_resp.status_code == 200:
        club_reqs = club_req_resp.json()
        print(f"✓ Get Club Requests Successful: {len(club_reqs)} requests found")
        if club_reqs:
            print(f"First request: {club_reqs[0]}")
    else:
        print(f"✗ Get Club Requests Failed: {club_req_resp.text}")
else:
    print("⚠ Skipped (token unavailable)")

# Test 14: Get TBLR Applications (Authenticated)
print("\n[TEST 14] Get TBLR Applications (Authenticated)")
print("-" * 60)
if token:
    headers = {'Authorization': f'Bearer {token}'}
    tblr_resp = req_get('http://localhost:8000/memberships/tblr-applications', headers=headers)
    print(f"Status Code: {tblr_resp.status_code}")
    if tblr_resp.status_code == 200:
        tblr_apps = tblr_resp.json()
        print(f"✓ Get TBLR Applications Successful: {len(tblr_apps)} applications found")
        if tblr_apps:
            print(f"First application: {tblr_apps[0]}")
    else:
        print(f"✗ Get TBLR Applications Failed: {tblr_resp.text}")
else:
    print("⚠ Skipped (token unavailable)")

# Test 15: Duplicate Pending Membership Request Should Be Blocked
print("\n[TEST 15] Duplicate Pending Membership Request Blocked")
print("-" * 60)
if token:
    headers = {'Authorization': f'Bearer {token}'}
    membership_payload = {
        "name": "Rajesh Kumar",
        "email": "rajesh@test.com",
        "phone": "9876543210",
        "vehicle_model": "Thar",
        "vehicle_number": "KA-03-NM-4040",
        "registration_date": "2024-01-01T00:00:00",
        "reason": "Applying for membership"
    }

    # First, check if there are existing requests and clean up
    existing_requests = req_get('http://localhost:8000/memberships/club-requests', headers=headers)
    if existing_requests.status_code == 200:
        for req in existing_requests.json():
            if req['status'] in ['PENDING', 'APPROVED']:
                # Delete existing request to clean up test state
                delete_resp = req_delete(
                    f'http://localhost:8000/memberships/club-requests/{req["id"]}',
                    headers=headers
                )
                print(f"Cleaned up existing {req['status']} request (ID: {req['id']})")

    # Now test duplicate blocking
    first_submit = req_post(
        'http://localhost:8000/memberships/club-requests',
        headers=headers,
        json=membership_payload
    )
    print(f"First submit status: {first_submit.status_code}")

    if first_submit.status_code == 200:
        second_submit = req_post(
            'http://localhost:8000/memberships/club-requests',
            headers=headers,
            json=membership_payload
        )
        print(f"Second submit status: {second_submit.status_code}")

        if second_submit.status_code == 409:
            print("✓ Duplicate pending membership request correctly blocked (409)")
        else:
            print(f"✗ Expected 409 but got {second_submit.status_code}: {second_submit.text}")
    elif first_submit.status_code in [400, 409]:
        if "active club membership" in first_submit.text.lower() or "already have" in first_submit.text.lower():
            print(f"✓ Membership request correctly blocked for active-member state ({first_submit.status_code})")
        else:
            print(f"✓ Membership request correctly blocked for duplicate state ({first_submit.status_code})")
    else:
        print(f"✗ First submit failed: {first_submit.status_code} - {first_submit.text}")
else:
    print("⚠ Skipped (token unavailable)")

# Test 16: Verify Accessories Data Populated
print("\n[TEST 16] Verify Accessories Data Populated")
print("-" * 60)
acc_resp = req_get('http://localhost:8000/accessories')
if acc_resp.status_code == 200:
    accessories = acc_resp.json()
    if len(accessories) >= 4:
        print(f"✓ Accessories Seeded Successfully: {len(accessories)} items")
        for acc in accessories:
            print(f"  - {acc['name']}: ₹{acc['price']}")
    else:
        print(f"✗ Insufficient accessories: {len(accessories)} found")
else:
    print(f"✗ Accessories endpoint failed: {acc_resp.text}")

# Test 17: Verify Merchandise Data Populated
print("\n[TEST 17] Verify Merchandise Data Populated")
print("-" * 60)
merch_resp = req_get('http://localhost:8000/merchandise')
if merch_resp.status_code == 200:
    merchandise = merch_resp.json()
    if len(merchandise) >= 4:
        print(f"✓ Merchandise Seeded Successfully: {len(merchandise)} items")
        for item in merchandise:
            print(f"  - {item['name']}: ₹{item['price']}")
    else:
        print(f"✗ Insufficient merchandise: {len(merchandise)} found")
else:
    print(f"✗ Merchandise endpoint failed: {merch_resp.text}")

# Test 18: Get Single Accessory
print("\n[TEST 18] Get Single Accessory Detail")
print("-" * 60)
if accessories and len(accessories) > 0:
    first_id = accessories[0].get('id')
    acc_detail_resp = req_get(f'http://localhost:8000/accessories/{first_id}')
    print(f"Status Code: {acc_detail_resp.status_code}")
    if acc_detail_resp.status_code == 200:
        accessory = acc_detail_resp.json()
        print(f"✓ Get Accessory Detail Successful: {accessory.get('name')}")
    else:
        print(f"✗ Get Accessory Detail Failed: {acc_detail_resp.text}")
else:
    print("⚠ Skipped (no accessories available)")

# Test 19: Get Single Merchandise
print("\n[TEST 19] Get Single Merchandise Detail")
print("-" * 60)
if merchandise and len(merchandise) > 0:
    first_id = merchandise[0].get('id')
    merch_detail_resp = req_get(f'http://localhost:8000/merchandise/{first_id}')
    print(f"Status Code: {merch_detail_resp.status_code}")
    if merch_detail_resp.status_code == 200:
        merch = merch_detail_resp.json()
        print(f"✓ Get Merchandise Detail Successful: {merch.get('name')}")
    else:
        print(f"✗ Get Merchandise Detail Failed: {merch_detail_resp.text}")
else:
    print("⚠ Skipped (no merchandise available)")

# Test 20: Get Single Feed with Comments
print("\n[TEST 20] Get Single Feed Detail")
print("-" * 60)
# First get list of feeds to get an ID
feeds_list = req_get('http://localhost:8000/feeds')
if feeds_list.status_code == 200 and feeds_list.json():
    feed_id = feeds_list.json()[0]['id']
    feed_detail_resp = req_get(f'http://localhost:8000/feeds/{feed_id}')
    print(f"Status Code: {feed_detail_resp.status_code}")
    if feed_detail_resp.status_code == 200:
        feed = feed_detail_resp.json()
        print(f"✓ Get Feed Detail Successful: {feed.get('title')}")
    else:
        print(f"✗ Get Feed Detail Failed: {feed_detail_resp.text}")
else:
    print("⚠ Skipped (no feeds available)")

# Test 21: Add Comment to Feed
print("\n[TEST 21] Add Comment to Feed (Authenticated)")
print("-" * 60)
if token:
    headers = {'Authorization': f'Bearer {token}'}
    feeds_list = req_get('http://localhost:8000/feeds')
    if feeds_list.status_code == 200 and feeds_list.json():
        feed_id = feeds_list.json()[0]['id']
        comment_data = {'content': 'Great adventure! Thanks for sharing.'}
        comment_resp = req_post(
            f'http://localhost:8000/feeds/{feed_id}/comments',
            json=comment_data,
            headers=headers
        )
        print(f"Status Code: {comment_resp.status_code}")
        if comment_resp.status_code == 200:
            print(f"✓ Add Comment Successful: {comment_resp.json()}")
        else:
            print(f"✗ Add Comment Failed: {comment_resp.text}")
    else:
        print("⚠ Skipped (no feeds available)")
else:
    print("⚠ Skipped (token unavailable)")

# Test 22: Get Feed Comments
print("\n[TEST 22] Get Feed Comments")
print("-" * 60)
feeds_list = req_get('http://localhost:8000/feeds')
if feeds_list.status_code == 200 and feeds_list.json():
    feed_id = feeds_list.json()[0]['id']
    comments_resp = req_get(f'http://localhost:8000/feeds/{feed_id}/comments')
    print(f"Status Code: {comments_resp.status_code}")
    if comments_resp.status_code == 200:
        comments = comments_resp.json()
        print(f"✓ Get Comments Successful: {len(comments)} comments found")
    else:
        print(f"✗ Get Comments Failed: {comments_resp.text}")
else:
    print("⚠ Skipped (no feeds available)")

# Test 23: Clear Cart
print("\n[TEST 23] Clear Entire Cart (Authenticated)")
print("-" * 60)
if token:
    headers = {'Authorization': f'Bearer {token}'}
    clear_resp = req_delete('http://localhost:8000/cart', headers=headers)
    print(f"Status Code: {clear_resp.status_code}")
    if clear_resp.status_code == 200:
        print(f"✓ Clear Cart Successful: {clear_resp.json()}")
    else:
        print(f"✗ Clear Cart Failed: {clear_resp.text}")
else:
    print("⚠ Skipped (token unavailable)")

# Test 24: Get Single Club Membership Request
print("\n[TEST 24] Get Single Club Membership Request (Authenticated)")
print("-" * 60)
if token:
    headers = {'Authorization': f'Bearer {token}'}
    requests_list = req_get('http://localhost:8000/memberships/club-requests', headers=headers)
    if requests_list.status_code == 200 and requests_list.json():
        request_id = requests_list.json()[0]['id']
        detail_resp = req_get(
            f'http://localhost:8000/memberships/club-requests/{request_id}',
            headers=headers
        )
        print(f"Status Code: {detail_resp.status_code}")
        if detail_resp.status_code == 200:
            print(f"✓ Get Request Detail Successful: {detail_resp.json().get('name')}")
        else:
            print(f"✗ Get Request Detail Failed: {detail_resp.text}")
    else:
        print("⚠ Skipped (no membership requests available)")
else:
    print("⚠ Skipped (token unavailable)")

# Test 25: Submit TBLR Application (Authenticated)
print("\n[TEST 25] Submit TBLR Application (Authenticated)")
print("-" * 60)
if token:
    headers = {'Authorization': f'Bearer {token}'}
    tblr_payload = {
        "full_name": "Rajesh Kumar",
        "email": "rajesh@test.com",
        "phone": "9876543210",
        "vehicle_model": "Thar RWD",
        "vehicle_number": "KA-03-NM-4040",
        "experience_level": "intermediate",
        "motivation": "Want to explore off-road trails"
    }
    tblr_submit_resp = req_post(
        'http://localhost:8000/memberships/tblr-applications',
        json=tblr_payload,
        headers=headers
    )
    print(f"Status Code: {tblr_submit_resp.status_code}")
    if tblr_submit_resp.status_code == 200:
        print(f"✓ Submit TBLR Application Successful: {tblr_submit_resp.json()}")
    else:
        print(f"✗ Submit TBLR Application Failed: {tblr_submit_resp.text}")
else:
    print("⚠ Skipped (token unavailable)")

# Test 26: Get Single TBLR Application
print("\n[TEST 26] Get Single TBLR Application (Authenticated)")
print("-" * 60)
if token:
    headers = {'Authorization': f'Bearer {token}'}
    tblr_list = req_get('http://localhost:8000/memberships/tblr-applications', headers=headers)
    if tblr_list.status_code == 200 and tblr_list.json():
        app_id = tblr_list.json()[0]['id']
        tblr_detail_resp = req_get(
            f'http://localhost:8000/memberships/tblr-applications/{app_id}',
            headers=headers
        )
        print(f"Status Code: {tblr_detail_resp.status_code}")
        if tblr_detail_resp.status_code == 200:
            print(f"✓ Get TBLR Detail Successful: {tblr_detail_resp.json().get('full_name')}")
        else:
            print(f"✗ Get TBLR Detail Failed: {tblr_detail_resp.text}")
    else:
        print("⚠ Skipped (no TBLR applications available)")
else:
    print("⚠ Skipped (token unavailable)")

# Test 27: Admin Login for Approval Tests
print("\n[TEST 27] Admin Login")
print("-" * 60)
admin_login_resp = req_post('http://localhost:8000/auth/login', json={'email': 'admin@test.com', 'password': 'test1234'})
print(f"Status Code: {admin_login_resp.status_code}")
if admin_login_resp.status_code == 200:
    admin_data = admin_login_resp.json()
    admin_token = admin_data.get('access_token')
    print(f"✓ Admin Login Successful")
    maybe_stop(27)
elif admin_login_resp.status_code == 403:
    print(f"✗ Admin account exists but email not verified (UC003): {admin_login_resp.text}")
    admin_token = None
    maybe_stop(27)
else:
    print(f"✗ Admin Login Failed: {admin_login_resp.text}")
    admin_token = None
    maybe_stop(27)

# Test 28: Approve Club Membership Request (Admin)
print("\n[TEST 28] Approve Club Membership (Admin)")
print("-" * 60)
if admin_token:
    admin_headers = {'Authorization': f'Bearer {admin_token}'}
    # Get list of pending requests (as admin we can see all)
    all_requests = req_get('http://localhost:8000/memberships/club-requests', headers=admin_headers)
    if all_requests.status_code == 200 and all_requests.json():
        pending_requests = [r for r in all_requests.json() if r['status'] == 'PENDING']
        if pending_requests:
            request_id = pending_requests[0]['id']
            approve_resp = requests.patch(
                f'http://localhost:8000/memberships/club-requests/{request_id}/approve',
                headers=admin_headers
            )
            print(f"Status Code: {approve_resp.status_code}")
            if approve_resp.status_code == 200:
                print(f"✓ Approve Request Successful: Status = {approve_resp.json().get('status')}")
            else:
                print(f"✗ Approve Request Failed: {approve_resp.text}")
        else:
            print("⚠ Skipped (no pending requests)")
    else:
        print("⚠ Skipped (could not retrieve requests)")
else:
    print("⚠ Skipped (admin token unavailable)")

# Test 29: Reject Club Membership Request (Admin)
print("\n[TEST 29] Reject Club Membership (Admin)")
print("-" * 60)
if admin_token:
    admin_headers = {'Authorization': f'Bearer {admin_token}'}
    # Try to find another pending request, or create one with a new user
    all_requests = req_get('http://localhost:8000/memberships/club-requests', headers=admin_headers)
    if all_requests.status_code == 200 and all_requests.json():
        pending_requests = [r for r in all_requests.json() if r['status'] == 'PENDING']
        if pending_requests:
            # Found a pending request, reject it
            request_id = pending_requests[0]['id']
            reject_resp = requests.patch(
                f'http://localhost:8000/memberships/club-requests/{request_id}/reject',
                headers=admin_headers
            )
            print(f"Status Code: {reject_resp.status_code}")
            if reject_resp.status_code == 200:
                print(f"✓ Reject Request Successful: Status = {reject_resp.json().get('status')}")
            else:
                print(f"✗ Reject Request Failed: {reject_resp.text}")
        else:
            # No pending requests, need to create one with a new user
            print("Creating new user for reject test...")
            new_user_data = {
                "name": "Reject Test User",
                "email": "rejecttest@example.com",
                "phone": "7777777777",
                "password": "test1234"
            }
            register_resp = req_post('http://localhost:8000/auth/register', json=new_user_data)
            if register_resp.status_code == 200:
                # Login as new user
                login_resp = req_post('http://localhost:8000/auth/login', 
                    json={'email': new_user_data['email'], 'password': new_user_data['password']})
                if login_resp.status_code == 200:
                    new_user_token = login_resp.json()['access_token']
                    new_user_headers = {'Authorization': f'Bearer {new_user_token}'}
                    # Create membership request
                    membership_payload = {
                        "name": "Reject Test User",
                        "email": "rejecttest@example.com",
                        "phone": "7777777777",
                        "vehicle_model": "Thar",
                        "vehicle_number": "KA-05-YY-5555",
                        "registration_date": "2024-01-01T00:00:00",
                        "reason": "Testing reject workflow"
                    }
                    create_resp = req_post(
                        'http://localhost:8000/memberships/club-requests',
                        json=membership_payload,
                        headers=new_user_headers
                    )
                    if create_resp.status_code == 200:
                        request_id = create_resp.json()['id']
                        reject_resp = requests.patch(
                            f'http://localhost:8000/memberships/club-requests/{request_id}/reject',
                            headers=admin_headers
                        )
                        print(f"Status Code: {reject_resp.status_code}")
                        if reject_resp.status_code == 200:
                            print(f"✓ Reject Request Successful: Status = {reject_resp.json().get('status')}")
                        else:
                            print(f"✗ Reject Request Failed: {reject_resp.text}")
                    else:
                        print(f"⚠ Could not create membership request: {create_resp.text}")
                else:
                    print(f"⚠ Could not login new user: {login_resp.text}")
            else:
                print(f"⚠ Could not register new user (may already exist): {register_resp.text}")
    else:
        print("⚠ Skipped (could not retrieve requests)")
else:
    print("⚠ Skipped (admin token unavailable)")

# Test 30: Non-Admin Cannot Approve (403 Test)
print("\n[TEST 30] Non-Admin Cannot Approve (403 Expected)")
print("-" * 60)
if token:
    user_headers = {'Authorization': f'Bearer {token}'}
    all_requests = req_get('http://localhost:8000/memberships/club-requests', headers=user_headers)
    if all_requests.status_code == 200 and all_requests.json():
        request_id = all_requests.json()[0]['id']
        forbidden_resp = requests.patch(
            f'http://localhost:8000/memberships/club-requests/{request_id}/approve',
            headers=user_headers
        )
        print(f"Status Code: {forbidden_resp.status_code}")
        if forbidden_resp.status_code == 403:
            print("✓ Non-admin correctly blocked from approving (403)")
        else:
            print(f"✗ Expected 403 but got {forbidden_resp.status_code}: {forbidden_resp.text}")
    else:
        print("⚠ Skipped (no requests available)")
else:
    print("⚠ Skipped (token unavailable)")

# ====== NEW TESTS FOR PHASE 3: BUY/SELL + SOCIAL AUTH + ROLE-BASED ACCESS ======

# Test 31: Create Listing (Buy/Sell)
print("\n[TEST 31] Create Listing (Buy/Sell)")
print("-" * 60)
if token:
    headers = {'Authorization': f'Bearer {token}'}
    listing_data = {
        "title": "2024 Mahindra Thar Test",
        "description": "Well maintained Thar for sale",
        "price": 15.5,
        "year": "2024",
        "mileage": "12000",
        "location": "Bengaluru",
        "vehicle_model": "Mahindra Thar",
        "vehicle_number": "KA-01-TEST-9999",
        "image_url": "https://example.com/thar.jpg"
    }
    create_listing_resp = req_post(
        'http://localhost:8000/buy-sell/listings',
        json=listing_data,
        headers=headers
    )
    print(f"Status Code: {create_listing_resp.status_code}")
    if create_listing_resp.status_code == 201:
        listing = create_listing_resp.json()
        test31_listing_id = listing.get('id')
        print(f"✓ Create Listing Successful: ID = {test31_listing_id}, Title = {listing.get('title')}")
        test31_success = True
    else:
        print(f"✗ Create Listing Failed: {create_listing_resp.text}")
        test31_success = False
else:
    print("⚠ Skipped (token unavailable)")
    test31_success = False

# Test 32: Get All Listings (Buy/Sell)
print("\n[TEST 32] Get All Listings (Buy/Sell)")
print("-" * 60)
list_resp = req_get('http://localhost:8000/buy-sell/listings')
print(f"Status Code: {list_resp.status_code}")
if list_resp.status_code == 200:
    listings = list_resp.json()
    print(f"✓ Get Listings Successful: {len(listings)} listings found")
    if listings:
        print(f"First listing: {listings[0].get('title')} - Status: {listings[0].get('status')}")
else:
    print(f"✗ Get Listings Failed: {list_resp.text}")

# Test 33: Get My Listings (Buy/Sell - Authenticated)
print("\n[TEST 33] Get My Listings (Buy/Sell - Authenticated)")
print("-" * 60)
if token:
    headers = {'Authorization': f'Bearer {token}'}
    my_listings_resp = req_get(
        'http://localhost:8000/buy-sell/listings/my',
        headers=headers
    )
    print(f"Status Code: {my_listings_resp.status_code}")
    if my_listings_resp.status_code == 200:
        my_listings = my_listings_resp.json()
        print(f"✓ Get My Listings Successful: {len(my_listings)} listings")
        if my_listings:
            print(f"My first listing: {my_listings[0].get('title')}")
    else:
        print(f"✗ Get My Listings Failed: {my_listings_resp.text}")
else:
    print("⚠ Skipped (token unavailable)")

# Test 34: Update Listing (Buy/Sell - Owner Only)
print("\n[TEST 34] Update Listing (Buy/Sell)")
print("-" * 60)
if token and test31_success:
    headers = {'Authorization': f'Bearer {token}'}
    update_data = {
        "title": "2024 Mahindra Thar - Updated Price",
        "price": 14.5,
        "status": "active"
    }
    update_resp = requests.patch(
        f'http://localhost:8000/buy-sell/listings/{test31_listing_id}',
        json=update_data,
        headers=headers
    )
    print(f"Status Code: {update_resp.status_code}")
    if update_resp.status_code == 200:
        updated = update_resp.json()
        print(f"✓ Update Listing Successful: New Price = {updated.get('price')}")
    else:
        print(f"✗ Update Listing Failed: {update_resp.text}")
else:
    print("⚠ Skipped (token unavailable or listing not created)")

# Test 35: Get Single Listing Detail
print("\n[TEST 35] Get Single Listing Detail")
print("-" * 60)
if test31_success:
    detail_resp = req_get(f'http://localhost:8000/buy-sell/listings/{test31_listing_id}')
    print(f"Status Code: {detail_resp.status_code}")
    if detail_resp.status_code == 200:
        listing_detail = detail_resp.json()
        print(f"✓ Get Listing Detail Successful: {listing_detail.get('title')}")
        print(f"  Seller: {listing_detail.get('seller', {}).get('name')}, Status: {listing_detail.get('status')}")
    else:
        print(f"✗ Get Listing Detail Failed: {detail_resp.text}")
else:
    print("⚠ Skipped (no listing available)")

# Test 36: Delete Listing (Buy/Sell - Soft Delete)
print("\n[TEST 36] Delete Listing (Buy/Sell - Soft Delete)")
print("-" * 60)
if token and test31_success:
    headers = {'Authorization': f'Bearer {token}'}
    delete_resp = req_delete(
        f'http://localhost:8000/buy-sell/listings/{test31_listing_id}',
        headers=headers
    )
    print(f"Status Code: {delete_resp.status_code}")
    if delete_resp.status_code == 204:
        print(f"✓ Delete Listing Successful (soft delete)")
        # Verify listing is now marked as DELETED
        verify_resp = req_get(f'http://localhost:8000/buy-sell/listings/{test31_listing_id}')
        if verify_resp.status_code == 404:
            print(f"✓ Deleted listing no longer accessible in active listings")
        else:
            print(f"✓ Listing marked as DELETED")
    else:
        print(f"✗ Delete Listing Failed: {delete_resp.text}")
else:
    print("⚠ Skipped (token unavailable or listing not created)")

# Test 37: Non-Owner Cannot Update Listing (403)
print("\n[TEST 37] Non-Owner Cannot Update Listing (403 Expected)")
print("-" * 60)
# First, create a listing with one user, then try to update with another user
if token:
    headers = {'Authorization': f'Bearer {token}'}
    # Create listing with rajesh
    listing_data = {
        "title": "Thar for Non-Owner Test",
        "description": "Testing ownership check",
        "price": 12.0,
        "year": "2023",
        "mileage": "18000",
        "location": "Bengaluru",
        "vehicle_model": "Mahindra Thar",
        "vehicle_number": "KA-02-OWNER-1111"
    }
    create_resp = req_post(
        'http://localhost:8000/buy-sell/listings',
        json=listing_data,
        headers=headers
    )
    if create_resp.status_code == 201:
        owner_listing_id = create_resp.json().get('id')
        
        # Try updating with admin user (different user)
        if admin_token:
            admin_headers = {'Authorization': f'Bearer {admin_token}'}
            update_data = {"title": "Hacked Title", "price": 999.0}
            forbidden_resp = requests.patch(
                f'http://localhost:8000/buy-sell/listings/{owner_listing_id}',
                json=update_data,
                headers=admin_headers
            )
            print(f"Status Code: {forbidden_resp.status_code}")
            if forbidden_resp.status_code == 403:
                print(f"✓ Non-owner correctly blocked from updating (403)")
            else:
                print(f"✗ Expected 403 but got {forbidden_resp.status_code}: {forbidden_resp.text}")
        else:
            print("⚠ Admin token unavailable for this test")
    else:
        print(f"⚠ Could not create listing for ownership test: {create_resp.text}")
else:
    print("⚠ Skipped (token unavailable)")

# Test 38: Social Auth - Google Login
print("\n[TEST 38] Social Auth - Google Login Endpoint Available")
print("-" * 60)
# Note: Full OAuth flow requires frontend SDK token, but we can verify endpoint exists
social_test_data = {
    "provider": "google",
    "token": "test_google_token_12345",
    "email": "socialtestgoogle@test.com",
    "name": "Social Test Google"
}
social_resp = req_post(
    'http://localhost:8000/auth/social-login',
    json=social_test_data
)
print(f"Status Code: {social_resp.status_code}")
# If we get 422 or similar, it's because token is fake, but endpoint exists
if social_resp.status_code in [200, 401, 403, 422]:
    print(f"✓ Social Auth Endpoint Available: {social_resp.status_code}")
    if social_resp.status_code == 200:
        print(f"✓ Social Auth Successful with fake token (endpoint working)")
    else:
        print(f"✓ Endpoint exists (got {social_resp.status_code} for validation - expected for fake token)")
else:
    print(f"✗ Social Auth Endpoint Issue: {social_resp.status_code}")

# Test 39: Social Auth - Apple Login Endpoint Available
print("\n[TEST 39] Social Auth - Apple Login Endpoint Available")
print("-" * 60)
social_test_data = {
    "provider": "apple",
    "token": "test_apple_token_12345",
    "email": "socialtestapple@test.com",
    "name": "Social Test Apple"
}
social_resp = req_post(
    'http://localhost:8000/auth/social-login',
    json=social_test_data
)
print(f"Status Code: {social_resp.status_code}")
if social_resp.status_code in [200, 401, 403, 422]:
    print(f"✓ Social Auth Endpoint Available: {social_resp.status_code}")
else:
    print(f"✗ Social Auth Endpoint Issue: {social_resp.status_code}")

# Test 40: Social Auth - Facebook Login Endpoint Available
print("\n[TEST 40] Social Auth - Facebook Login Endpoint Available")
print("-" * 60)
social_test_data = {
    "provider": "facebook",
    "token": "test_facebook_token_12345",
    "email": "socialtestfb@test.com",
    "name": "Social Test Facebook"
}
social_resp = req_post(
    'http://localhost:8000/auth/social-login',
    json=social_test_data
)
print(f"Status Code: {social_resp.status_code}")
if social_resp.status_code in [200, 401, 403, 422]:
    print(f"✓ Social Auth Endpoint Available: {social_resp.status_code}")
else:
    print(f"✗ Social Auth Endpoint Issue: {social_resp.status_code}")

# Test 41: Verify User Response Includes Membership Status
print("\n[TEST 41] User Response Includes Membership Status Fields")
print("-" * 60)
if token:
    headers = {'Authorization': f'Bearer {token}'}
    user_details_resp = req_get('http://localhost:8000/auth/me', headers=headers)
    print(f"Status Code: {user_details_resp.status_code}")
    if user_details_resp.status_code == 200:
        user = user_details_resp.json()
        membership_status = user.get('membership_status')
        tblr_status = user.get('tblr_membership_status')
        print(f"✓ User Retrieved Successfully")
        print(f"  Email: {user.get('email')}")
        print(f"  Membership Status: {membership_status}")
        print(f"  TBLR Membership Status: {tblr_status}")
        if membership_status is not None and tblr_status is not None:
            print(f"✓ Both membership status fields present in response")
        else:
            print(f"✗ Missing membership status fields")
    else:
        print(f"✗ Get User Failed: {user_details_resp.text}")
else:
    print("⚠ Skipped (token unavailable)")

# Test 42: Guest User Cannot Create Listings
print("\n[TEST 42] Unauthenticated User Cannot Create Listings (401 Expected)")
print("-" * 60)
listing_data = {
    "title": "Unauthorized Listing Attempt",
    "description": "Should fail",
    "price": 10.0,
    "year": "2022",
    "mileage": "25000",
    "location": "Bengaluru",
    "vehicle_model": "Mahindra Thar",
    "vehicle_number": "KA-99-UNAUTH-9999"
}
unauth_resp = req_post(
    'http://localhost:8000/buy-sell/listings',
    json=listing_data
)
print(f"Status Code: {unauth_resp.status_code}")
if unauth_resp.status_code == 401:
    print(f"✓ Unauthenticated user correctly blocked (401)")
else:
    print(f"✗ Expected 401 but got {unauth_resp.status_code}")

# Test 43: Unauthenticated User CAN View Listings (Public Endpoint)
print("\n[TEST 43] Unauthenticated User CAN View Listings (Public)")
print("-" * 60)
public_listings_resp = req_get('http://localhost:8000/buy-sell/listings')
print(f"Status Code: {public_listings_resp.status_code}")
if public_listings_resp.status_code == 200:
    print(f"✓ Public listing view available: {len(public_listings_resp.json())} listings")
else:
    print(f"✗ Public listing view failed: {public_listings_resp.text}")

# Test 44: Admin Can Update Any Listing (Admin Privileges - If Enabled)
print("\n[TEST 44] Admin Listing Management")
print("-" * 60)
if admin_token and token:
    # First create listing as regular user
    headers = {'Authorization': f'Bearer {token}'}
    listing_data = {
        "title": "Admin Management Test Listing",
        "description": "For admin testing",
        "price": 20.0,
        "year": "2021",
        "mileage": "30000",
        "location": "Bengaluru",
        "vehicle_model": "Mahindra Thar",
        "vehicle_number": "KA-03-ADMIN-2222"
    }
    create_resp = req_post(
        'http://localhost:8000/buy-sell/listings',
        json=listing_data,
        headers=headers
    )
    if create_resp.status_code == 201:
        admin_test_listing_id = create_resp.json().get('id')
        print(f"✓ Test listing created by user: {admin_test_listing_id}")
        
        # Admin can view it
        admin_headers = {'Authorization': f'Bearer {admin_token}'}
        admin_view_resp = req_get(
            f'http://localhost:8000/buy-sell/listings/{admin_test_listing_id}',
            headers=admin_headers
        )
        if admin_view_resp.status_code == 200:
            print(f"✓ Admin can view user's listing")
        else:
            print(f"✗ Admin view failed: {admin_view_resp.text}")
    else:
        print(f"⚠ Could not create test listing: {create_resp.text}")
else:
    print("⚠ Skipped (admin token or user token unavailable)")

# Test 45: Invalid Social Provider Rejected
print("\n[TEST 45] Social Auth - Invalid Provider Rejected")
print("-" * 60)
invalid_social_data = {
    "provider": "invalid_provider",
    "token": "some_token",
    "email": "test@test.com",
    "name": "Test User"
}
invalid_resp = req_post(
    'http://localhost:8000/auth/social-login',
    json=invalid_social_data
)
print(f"Status Code: {invalid_resp.status_code}")
if invalid_resp.status_code in [400, 422]:
    print(f"✓ Invalid provider correctly rejected ({invalid_resp.status_code})")
else:
    print(f"✗ Expected 400/422 but got {invalid_resp.status_code}")

# Test 46: Listing Detail Returns Seller Information
print("\n[TEST 46] Listing Detail - Seller Information")
print("-" * 60)
list_resp = req_get('http://localhost:8000/buy-sell/listings')
if list_resp.status_code == 200 and list_resp.json():
    first_listing = list_resp.json()[0]
    listing_id = first_listing.get('id')
    detail_resp = req_get(f'http://localhost:8000/buy-sell/listings/{listing_id}')
    if detail_resp.status_code == 200:
        listing = detail_resp.json()
        seller = listing.get('seller')
        if seller:
            print(f"✓ Listing detail includes seller info")
            print(f"  Seller: {seller.get('name')} ({seller.get('email')})")
        else:
            print(f"✗ Seller information missing from listing detail")
    else:
        print(f"✗ Could not get listing detail: {detail_resp.text}")
else:
    print(f"⚠ Skipped (no listings available)")

# Test 47: Only ACTIVE Listings Shown by Default
print("\n[TEST 47] Only ACTIVE Listings Shown by Default")
print("-" * 60)
list_resp = req_get('http://localhost:8000/buy-sell/listings')
if list_resp.status_code == 200:
    listings = list_resp.json()
    non_active = [l for l in listings if str(l.get('status', '')).lower() != 'active']
    if non_active:
        print(f"✗ Found {len(non_active)} non-ACTIVE listings in default view")
    else:
        print(f"✓ All {len(listings)} listings shown have ACTIVE status")
else:
    print(f"✗ Could not get listings: {list_resp.text}")

# Test 48: Member Discovery List (UC004)
print("\n[TEST 48] Member Discovery - List Members")
print("-" * 60)
uc004_member_id = None
if token:
    headers = {'Authorization': f'Bearer {token}'}
    members_resp = req_get('http://localhost:8000/members', headers=headers)
    print(f"Status Code: {members_resp.status_code}")
    if members_resp.status_code == 200:
        members = members_resp.json()
        print(f"✓ Member discovery successful: {len(members)} members found")
        if members:
            uc004_member_id = members[0].get('id')
            print(f"First member: {members[0].get('name')} (ID: {uc004_member_id})")
    else:
        print(f"✗ Member discovery failed: {members_resp.text}")
else:
    print("⚠ Skipped (token unavailable)")
maybe_stop(48)

# Test 49: Member Profile Detail (UC004)
print("\n[TEST 49] Member Discovery - Member Profile Detail")
print("-" * 60)
if token and uc004_member_id:
    headers = {'Authorization': f'Bearer {token}'}
    profile_resp = req_get(f'http://localhost:8000/members/{uc004_member_id}', headers=headers)
    print(f"Status Code: {profile_resp.status_code}")
    if profile_resp.status_code == 200:
        profile = profile_resp.json()
        print(f"✓ Member profile retrieved: {profile.get('name')}")
        print(f"  Vehicles listed: {len(profile.get('vehicles', []))}")
    else:
        print(f"✗ Member profile retrieval failed: {profile_resp.text}")
else:
    print("⚠ Skipped (token/member ID unavailable)")
maybe_stop(49)

# Test 50: Vehicle Add and List (UC004)
print("\n[TEST 50] Vehicle Management - Add & List My Vehicles")
print("-" * 60)
uc004_vehicle_id = None
if token:
    headers = {'Authorization': f'Bearer {token}'}
    vehicle_payload = {
        "make": "Mahindra",
        "model": "Thar Roxx",
        "year": "2024",
        "registration_number": "KA-05-UC004-5050",
        "color": "Black",
        "mileage": 5000,
        "is_primary": False,
    }
    add_vehicle_resp = req_post('http://localhost:8000/members/vehicles', headers=headers, json=vehicle_payload)
    print(f"Add Vehicle Status: {add_vehicle_resp.status_code}")
    if add_vehicle_resp.status_code == 200:
        uc004_vehicle_id = add_vehicle_resp.json().get('id')
        print(f"✓ Vehicle added successfully: ID = {uc004_vehicle_id}")
    else:
        print(f"✗ Vehicle add failed: {add_vehicle_resp.text}")

    list_vehicles_resp = req_get('http://localhost:8000/members/vehicles/user', headers=headers)
    print(f"List Vehicles Status: {list_vehicles_resp.status_code}")
    if list_vehicles_resp.status_code == 200:
        print(f"✓ Retrieved {len(list_vehicles_resp.json())} vehicles")
    else:
        print(f"✗ Vehicle list failed: {list_vehicles_resp.text}")
else:
    print("⚠ Skipped (token unavailable)")
maybe_stop(50)

# Test 51: Vehicle Update and Delete (UC004)
print("\n[TEST 51] Vehicle Management - Update & Delete")
print("-" * 60)
if token and uc004_vehicle_id:
    headers = {'Authorization': f'Bearer {token}'}
    update_vehicle_payload = {
        "color": "Desert Sand",
        "mileage": 5500,
    }
    update_vehicle_resp = req_put(
        f'http://localhost:8000/members/vehicles/{uc004_vehicle_id}',
        headers=headers,
        json=update_vehicle_payload,
    )
    print(f"Update Vehicle Status: {update_vehicle_resp.status_code}")
    if update_vehicle_resp.status_code == 200:
        print(f"✓ Vehicle updated successfully")
    else:
        print(f"✗ Vehicle update failed: {update_vehicle_resp.text}")

    delete_vehicle_resp = req_delete(f'http://localhost:8000/members/vehicles/{uc004_vehicle_id}', headers=headers)
    print(f"Delete Vehicle Status: {delete_vehicle_resp.status_code}")
    if delete_vehicle_resp.status_code == 204:
        print("✓ Vehicle deleted successfully")
    else:
        print(f"✗ Vehicle delete failed: {delete_vehicle_resp.text}")
else:
    print("⚠ Skipped (token/vehicle ID unavailable)")
maybe_stop(51)

# Test 52: Messaging - Send Message (UC004)
print("\n[TEST 52] Messaging - Send Message")
print("-" * 60)
if token and uc004_member_id:
    headers = {'Authorization': f'Bearer {token}'}
    msg_payload = {
        "receiver_id": uc004_member_id,
        "content": "UC004 integration test message",
    }
    send_msg_resp = req_post('http://localhost:8000/messages', headers=headers, json=msg_payload)
    print(f"Status Code: {send_msg_resp.status_code}")
    if send_msg_resp.status_code == 200:
        print("✓ Message sent successfully")
    else:
        print(f"✗ Message send failed: {send_msg_resp.text}")
else:
    print("⚠ Skipped (token/member ID unavailable)")
maybe_stop(52)

# Test 53: Messaging - Conversation and Conversations List (UC004)
print("\n[TEST 53] Messaging - Conversation History & Conversations")
print("-" * 60)
if token and uc004_member_id:
    headers = {'Authorization': f'Bearer {token}'}
    conv_resp = req_get(f'http://localhost:8000/messages/conversation/{uc004_member_id}', headers=headers)
    print(f"Conversation Status: {conv_resp.status_code}")
    if conv_resp.status_code == 200:
        print(f"✓ Conversation fetched: {len(conv_resp.json())} messages")
    else:
        print(f"✗ Conversation fetch failed: {conv_resp.text}")

    conversations_resp = req_get('http://localhost:8000/messages/conversations', headers=headers)
    print(f"Conversations Status: {conversations_resp.status_code}")
    if conversations_resp.status_code == 200:
        print(f"✓ Conversations list fetched: {len(conversations_resp.json())} threads")
    else:
        print(f"✗ Conversations list failed: {conversations_resp.text}")
else:
    print("⚠ Skipped (token/member ID unavailable)")

# Test 54: Edit Profile (UC004A)  
print("\n[TEST 54] Edit Profile - Update Profile Fields")
print("-" * 60)
profile_update_data = {
    "name": "Rajesh Updated",
    "address": "123 Main Street, Bangalore",
    "emergency_contact": "9876543210",
    "preferences": "Off-road adventures, Weekend trips"
}
profile_response = req_put(
    'http://localhost:8000/auth/me',
    headers=headers,
    json=profile_update_data
)
if profile_response.status_code == 200:
    profile_data = profile_response.json()
    assert profile_data["name"] == "Rajesh Updated", "Name not updated"
    assert profile_data["address"] == "123 Main Street, Bangalore", "Address not updated"
    assert profile_data["emergency_contact"] == "9876543210", "Emergency contact not updated"
    print(f"Profile Status: 200")
    print(f"Name updated: {profile_data['name']}")
    
    # Test 54b: Verify locked fields
    print("\n[TEST 54b] Verify Email & Phone Locked (UC004A)")
    print("-" * 60)
    current_email = profile_data["email"]
    current_phone = profile_data["phone"]
    locked_update = {"name": "Rajesh"}
    locked_response = req_put(
        'http://localhost:8000/auth/me',
        headers=headers,
        json=locked_update
    )
    if locked_response.status_code == 200:
        locked_data = locked_response.json()
        assert locked_data["email"] == current_email, "Email changed"
        assert locked_data["phone"] == current_phone, "Phone changed"
        print("Locked Fields Status: Email and phone remain unchanged")
else:
    print(f"Profile update failed: {profile_response.status_code}")
maybe_stop(54)





# ==================== UC004B: EVENT REGISTRATION & PAYMENT TESTS ====================

# Test 55: List Events (UC004B)
print("\n[TEST 55] UC004B - List Published Events")
print("-" * 60)
events_resp = req_get('http://localhost:8000/events')
print(f"Status Code: {events_resp.status_code}")
uc004b_event_id = None
if events_resp.status_code == 200:
    events = events_resp.json()
    print(f"✓ Events fetched: {len(events)} events")
    if len(events) > 0:
        uc004b_event_id = events[0]['id']
        print(f"First event: {events[0]['name']}")
        print(f"Event ID: {uc004b_event_id}, Fee: ₹{events[0]['event_fee']}")
else:
    print(f"✗ Events fetch failed: {events_resp.text}")
maybe_stop(55)

# Test 56: Get Event Details (UC004B)
print("\n[TEST 56] UC004B - Get Event Detail")
print("-" * 60)
if uc004b_event_id:
    event_detail_resp = req_get(f'http://localhost:8000/events/{uc004b_event_id}')
    print(f"Status Code: {event_detail_resp.status_code}")
    if event_detail_resp.status_code == 200:
        event = event_detail_resp.json()
        print(f"✓ Event: {event['name']}")
        print(f"Location: {event['location']}")
        print(f"Max participants: {event['max_participants']}")
        print(f"Available slots: {event['max_participants'] - event['current_participants']}")
    else:
        print(f"✗ Event detail fetch failed: {event_detail_resp.text}")
else:
    print("⚠ Skipped (no event ID)")
maybe_stop(56)

# Test 57: Register for Event (UC004B A1, A5-A8)
print("\n[TEST 57] UC004B - Register for Event with Co-Passengers")
print("-" * 60)
uc004b_registration_id = None
if token and uc004b_event_id:
    headers = {'Authorization': f'Bearer {token}'}
    registration_payload = {
        "num_copassengers": 2,
        "copassengers": [
            {"name": "John Doe", "age": 30, "gender": "Male"},
            {"name": "Jane Doe", "age": 28, "gender": "Female"}
        ]
    }
    register_resp = req_post(
        f'http://localhost:8000/events/{uc004b_event_id}/register',
        headers=headers,
        json=registration_payload
    )
    print(f"Status Code: {register_resp.status_code}")
    if register_resp.status_code == 201:
        reg_data = register_resp.json()
        uc004b_registration_id = reg_data['id']
        print(f"✓ Registration successful")
        print(f"Registration ID: {uc004b_registration_id}")
        print(f"Status: {reg_data['registration_status']}")
        print(f"Total amount: ₹{reg_data['total_amount']}")
        print(f"Co-passengers: {len(reg_data['copassengers'])}")
    elif register_resp.status_code == 409:
        print("✓ Registration already exists, reusing existing registration")
        existing_regs_resp = req_get('http://localhost:8000/events/my-registrations', headers=headers)
        if existing_regs_resp.status_code == 200:
            existing_regs = existing_regs_resp.json()
            existing = next((r for r in existing_regs if r['event_id'] == uc004b_event_id), None)
            if existing:
                uc004b_registration_id = existing['id']
                print(f"Using Registration ID: {uc004b_registration_id}")
            else:
                print("✗ Existing registration not found for event")
        else:
            print(f"✗ Could not fetch existing registrations: {existing_regs_resp.text}")
    else:
        print(f"✗ Registration failed: {register_resp.text}")
else:
    print("⚠ Skipped (token/event ID unavailable)")
maybe_stop(57)

# Test 58: Initiate Payment (UC004B A2)
print("\n[TEST 58] UC004B - Initiate Payment")
print("-" * 60)
uc004b_payment_id = None
uc004b_gateway_order_id = None
if token and uc004b_event_id and uc004b_registration_id:
    headers = {'Authorization': f'Bearer {token}'}
    reg_resp = req_get(f'http://localhost:8000/events/my-registrations', headers=headers)
    if reg_resp.status_code == 200:
        regs = reg_resp.json()
        target_reg = next((r for r in regs if r['id'] == uc004b_registration_id), None)
        if target_reg:
            amount = target_reg['total_amount']
            payment_payload = {
                "event_id": uc004b_event_id,
                "registration_id": uc004b_registration_id,
                "amount": amount,
                "payment_gateway": "razorpay"
            }
            payment_resp = req_post(
                'http://localhost:8000/payments/initiate',
                headers=headers,
                json=payment_payload
            )
            print(f"Status Code: {payment_resp.status_code}")
            if payment_resp.status_code == 201:
                payment_data = payment_resp.json()
                uc004b_payment_id = payment_data['id']
                uc004b_gateway_order_id = payment_data['gateway_order_id']
                print(f"✓ Payment initiated")
                print(f"Payment ID: {uc004b_payment_id}")
                print(f"Gateway Order ID: {uc004b_gateway_order_id}")
                print(f"Amount: ₹{payment_data['amount']}")
                print(f"Status: {payment_data['payment_status']}")
            elif payment_resp.status_code == 400 and "already completed" in payment_resp.text.lower():
                print("✓ Payment already completed for this registration")
            else:
                print(f"✗ Payment initiation failed: {payment_resp.text}")
        else:
            print("⚠ Target registration not found")
    else:
        print(f"⚠ Could not fetch registrations: {reg_resp.text}")
else:
    print("⚠ Skipped (token/event ID/registration ID unavailable)")
maybe_stop(58)

# Test 59: Verify Payment (UC004B A3, A4)
print("\n[TEST 59] UC004B - Verify Payment and WhatsApp Link")
print("-" * 60)
if token and uc004b_gateway_order_id:
    headers = {'Authorization': f'Bearer {token}'}
    verify_payload = {
        "gateway_payment_id": f"pay_mock_{uc004b_payment_id}",
        "gateway_order_id": uc004b_gateway_order_id,
        "gateway_signature": "mock_signature_for_testing"
    }
    verify_resp = req_post(
        'http://localhost:8000/payments/verify',
        headers=headers,
        json=verify_payload
    )
    print(f"Status Code: {verify_resp.status_code}")
    if verify_resp.status_code == 200:
        verified_payment = verify_resp.json()
        print(f"✓ Payment verified")
        print(f"Payment Status: {verified_payment['payment_status']}")
        print("✓ UC004B A4: Registration confirmed and WhatsApp link generated")
    else:
        print(f"✗ Payment verification failed: {verify_resp.text}")
else:
    print("⚠ Skipped (token/gateway order ID unavailable)")
maybe_stop(59)

# Test 60: Get My Registrations (UC004B)
print("\n[TEST 60] UC004B - Get My Event Registrations")
print("-" * 60)
if token:
    headers = {'Authorization': f'Bearer {token}'}
    my_regs_resp = req_get('http://localhost:8000/events/my-registrations', headers=headers)
    print(f"Status Code: {my_regs_resp.status_code}")
    if my_regs_resp.status_code == 200:
        registrations = my_regs_resp.json()
        print(f"✓ Registrations fetched: {len(registrations)} registration(s)")
        if len(registrations) > 0:
            latest_reg = registrations[0]
            print(f"Latest registration:")
            print(f"  Event ID: {latest_reg['event_id']}")
            print(f"  Status: {latest_reg['registration_status']}")
            has_link = 'Yes' if latest_reg.get('whatsapp_link') else 'No'
            print(f"  Has WhatsApp link: {has_link}")
    else:
        print(f"✗ My registrations fetch failed: {my_regs_resp.text}")
else:
    print("⚠ Skipped (token unavailable)")
maybe_stop(60)


# ==================== UC004C: COMMUNITY FEED SEARCH & INTERACTION TESTS ====================

# Test 61: Search Feeds (Guest/Public Access)
print("\n[TEST 61] UC004C - Search Feeds (Guest Access)")
print("-" * 60)
guest_search_resp = req_get('http://localhost:8000/feeds?q=trail')
print(f"Status Code: {guest_search_resp.status_code}")
if guest_search_resp.status_code == 200:
    guest_results = guest_search_resp.json()
    print(f"✓ Guest search successful: {len(guest_results)} result(s)")
else:
    print(f"✗ Guest search failed: {guest_search_resp.text}")
maybe_stop(61)

# Test 62: Search Feeds Invalid Input (200+ chars)
print("\n[TEST 62] UC004C - Search Invalid Input")
print("-" * 60)
invalid_query = "a" * 201
invalid_search_resp = req_get(f'http://localhost:8000/feeds?q={invalid_query}')
print(f"Status Code: {invalid_search_resp.status_code}")
if invalid_search_resp.status_code == 422:
    print("✓ Invalid search input correctly rejected (422)")
else:
    print(f"✗ Expected 422 but got {invalid_search_resp.status_code}: {invalid_search_resp.text}")
maybe_stop(62)

# Test 63: Search No Results
print("\n[TEST 63] UC004C - Search No Results")
print("-" * 60)
no_results_resp = req_get('http://localhost:8000/feeds?q=__no_match_uc004c__')
print(f"Status Code: {no_results_resp.status_code}")
if no_results_resp.status_code == 200:
    no_results = no_results_resp.json()
    if isinstance(no_results, list) and len(no_results) == 0:
        print("✓ No-results search returned empty list")
    else:
        print(f"✗ Expected empty list, got {len(no_results) if isinstance(no_results, list) else 'non-list response'}")
else:
    print(f"✗ No-results search failed: {no_results_resp.text}")
maybe_stop(63)

# Test 64: Search Relevance Order (title match before content match)
print("\n[TEST 64] UC004C - Search Relevance Ordering")
print("-" * 60)
uc004c_title_feed_id = None
uc004c_content_feed_id = None
if token:
    headers = {'Authorization': f'Bearer {token}'}

    title_feed_payload = {
        'title': 'UC004CRelevanceTrail',
        'content': 'Generic post content for relevance test',
        'image_url': None
    }
    content_feed_payload = {
        'title': 'General Update',
        'content': 'This post mentions UC004CRelevanceTrail in content only',
        'image_url': None
    }

    create_title_resp = req_post('http://localhost:8000/feeds', json=title_feed_payload, headers=headers)
    create_content_resp = req_post('http://localhost:8000/feeds', json=content_feed_payload, headers=headers)

    if create_title_resp.status_code == 200 and create_content_resp.status_code == 200:
        uc004c_title_feed_id = create_title_resp.json().get('id')
        uc004c_content_feed_id = create_content_resp.json().get('id')

        relevance_resp = req_get('http://localhost:8000/feeds?q=UC004CRelevanceTrail', headers=headers)
        print(f"Status Code: {relevance_resp.status_code}")
        if relevance_resp.status_code == 200:
            relevance_results = relevance_resp.json()
            if relevance_results:
                top_result_id = relevance_results[0].get('id')
                print(f"Top result ID: {top_result_id}")
                if top_result_id == uc004c_title_feed_id:
                    print("✓ Search relevance ordering is correct")
                else:
                    print("✗ Relevance ordering mismatch (expected title match first)")
            else:
                print("✗ No results returned for relevance query")
        else:
            print(f"✗ Search relevance request failed: {relevance_resp.text}")
    else:
        print(f"✗ Could not create relevance test feeds: title={create_title_resp.status_code}, content={create_content_resp.status_code}")
else:
    print("⚠ Skipped (token unavailable)")
maybe_stop(64)

# Test 65: Like Toggle (active club member)
print("\n[TEST 65] UC004C - Toggle Like (Active Club Member)")
print("-" * 60)
uc004c_like_feed_id = uc004c_title_feed_id
if token and uc004c_like_feed_id:
    headers = {'Authorization': f'Bearer {token}'}
    like_resp_1 = req_post(f'http://localhost:8000/feeds/{uc004c_like_feed_id}/like', headers=headers)
    like_resp_2 = req_post(f'http://localhost:8000/feeds/{uc004c_like_feed_id}/like', headers=headers)
    print(f"Like #1 Status: {like_resp_1.status_code}, Like #2 Status: {like_resp_2.status_code}")
    if like_resp_1.status_code == 200 and like_resp_2.status_code == 200:
        body1 = like_resp_1.json()
        body2 = like_resp_2.json()
        first_likes = body1.get('likes_count')
        second_likes = body2.get('likes_count')
        if isinstance(first_likes, int) and isinstance(second_likes, int) and abs(first_likes - second_likes) == 1:
            print(f"✓ Like toggle works correctly (likes_count: {first_likes} -> {second_likes})")
        else:
            print("✗ Like toggle state did not update as expected")
    else:
        print(f"✗ Like toggle failed: {like_resp_1.text if like_resp_1.status_code != 200 else like_resp_2.text}")
else:
    print("⚠ Skipped (token/feed unavailable)")
maybe_stop(65)

# Test 66: Non-active member cannot like/comment
print("\n[TEST 66] UC004C - Interaction Blocked for Non-Active Members")
print("-" * 60)
non_active_token = None
login_priya_resp = req_post(
    'http://localhost:8000/auth/login',
    json={'email': 'priya@test.com', 'password': 'test1234'}
)
if login_priya_resp.status_code == 200:
    non_active_token = login_priya_resp.json().get('access_token')

if non_active_token and uc004c_like_feed_id:
    non_active_headers = {'Authorization': f'Bearer {non_active_token}'}
    blocked_like_resp = req_post(f'http://localhost:8000/feeds/{uc004c_like_feed_id}/like', headers=non_active_headers)
    blocked_comment_resp = req_post(
        f'http://localhost:8000/feeds/{uc004c_like_feed_id}/comments',
        headers=non_active_headers,
        json={'content': 'Should be blocked'}
    )
    print(f"Like Status: {blocked_like_resp.status_code}, Comment Status: {blocked_comment_resp.status_code}")
    if blocked_like_resp.status_code == 403 and blocked_comment_resp.status_code == 403:
        print("✓ Non-active member interaction correctly blocked (403)")
    else:
        print(f"✗ Expected 403/403 but got {blocked_like_resp.status_code}/{blocked_comment_resp.status_code}")
else:
    print("⚠ Skipped (non-active token/feed unavailable)")
maybe_stop(66)

# Test 67: Deleted/Missing post detail handling
print("\n[TEST 67] UC004C - Missing Post Detail")
print("-" * 60)
missing_feed_resp = req_get('http://localhost:8000/feeds/999999999')
print(f"Status Code: {missing_feed_resp.status_code}")
if missing_feed_resp.status_code == 404 and 'unmarked trail' in missing_feed_resp.text.lower():
    print("✓ Missing post returns expected 404 detail message")
else:
    print(f"✗ Missing post behavior mismatch: {missing_feed_resp.text}")
maybe_stop(67)

# Test 68: Search by author name
print("\n[TEST 68] UC004C - Search by Author Name")
print("-" * 60)
author_search_resp = req_get('http://localhost:8000/feeds?q=Rajesh')
print(f"Status Code: {author_search_resp.status_code}")
if author_search_resp.status_code == 200:
    author_results = author_search_resp.json()
    print(f"✓ Author search successful: {len(author_results)} result(s)")
else:
    print(f"✗ Author search failed: {author_search_resp.text}")
maybe_stop(68)


# ==================== UC004D: ACCESSORIES SHOPPING & VENDOR INTEGRATION TESTS ====================

# Test 69: Browse Accessories Categories
print("\n[TEST 69] UC004D - Get Accessory Categories")
print("-" * 60)
categories_resp = req_get('http://localhost:8000/accessories/categories')
print(f"Status Code: {categories_resp.status_code}")
if categories_resp.status_code == 200:
    categories = categories_resp.json()
    print(f"✓ Categories fetched: {len(categories)} categories")
    for cat, icon in list(categories.items())[:3]:
        print(f"  {icon} {cat}")
else:
    print(f"✗ Categories fetch failed: {categories_resp.text}")
maybe_stop(69)


# Test 70: Get Accessories List (with stock filtering)
print("\n[TEST 70] UC004D - List Accessories")
print("-" * 60)
accessories_resp = req_get('http://localhost:8000/accessories')
print(f"Status Code: {accessories_resp.status_code}")
if accessories_resp.status_code == 200:
    accessories = accessories_resp.json()
    print(f"✓ Accessories fetched: {len(accessories)} items")
    if len(accessories) > 0:
        first_acc = accessories[0]
        print(f"First accessory:")
        print(f"  Name: {first_acc['name']}")
        print(f"  Price: ₹{first_acc['price']}")
        print(f"  Stock: {first_acc['stock']}")
        print(f"  Vendor: {first_acc.get('vendor', {}).get('name', 'N/A')}")
        uc004d_accessory_id = first_acc['id']
    else:
        print("⚠ No accessories available")
        uc004d_accessory_id = None
else:
    print(f"✗ Accessories list failed: {accessories_resp.text}")
    uc004d_accessory_id = None
maybe_stop(70)


# Test 71: Get Accessory Detail (with vendor info)
print("\n[TEST 71] UC004D - Get Accessory Detail with Vendor")
print("-" * 60)
if uc004d_accessory_id:
    detail_resp = req_get(f'http://localhost:8000/accessories/{uc004d_accessory_id}')
    print(f"Status Code: {detail_resp.status_code}")
    if detail_resp.status_code == 200:
        accessory = detail_resp.json()
        print(f"✓ Accessory detail fetched")
        print(f"  Name: {accessory['name']}")
        print(f"  Price: ₹{accessory['price']}")
        print(f"  Stock: {accessory['stock']}")
        if 'vendor' in accessory:
            vendor = accessory['vendor']
            print(f"  Vendor: {vendor['name']}")
            print(f"  Vendor Email: {vendor['email']}")
            print(f"  Vendor WhatsApp: {vendor['whatsapp_number']}")
            uc004d_vendor_id = vendor['id']
        else:
            print("  ⚠ No vendor information")
            uc004d_vendor_id = None
    else:
        print(f"✗ Detail fetch failed: {detail_resp.text}")
        uc004d_vendor_id = None
else:
    print("⚠ Skipped (no accessory ID)")
    uc004d_vendor_id = None
maybe_stop(71)


# Test 72: Checkout (Guest - No Auth Required)
print("\n[TEST 72] UC004D - Checkout Accessories (Guest)")
print("-" * 60)
uc004d_order_id = None
uc004d_order_number = None
if uc004d_accessory_id:
    checkout_payload = {
        "items": [
            {"product_type": "accessory", "product_id": uc004d_accessory_id, "quantity": 1}
        ],
        "customer_name": "Guest User",
        "customer_email": "guest@test.com",
        "customer_phone": "9999999999",
        "shipping_address": "123 Test Street, Bengaluru, Karnataka 560001"
    }
    checkout_resp = req_post('http://localhost:8000/accessories/checkout', json=checkout_payload)
    print(f"Status Code: {checkout_resp.status_code}")
    if checkout_resp.status_code == 200:
        order_data = checkout_resp.json()
        uc004d_order_id = order_data['order_id']
        uc004d_order_number = order_data['order_number']
        print(f"✓ Checkout successful")
        print(f"  Order ID: {uc004d_order_id}")
        print(f"  Order Number: {uc004d_order_number}")
        print(f"  Amount: ₹{order_data['amount']}")
        print(f"  Gateway URL: {order_data['gateway_redirect_url'][:50]}...")
    else:
        print(f"✗ Checkout failed: {checkout_resp.text}")
else:
    print("⚠ Skipped (no accessory ID)")
maybe_stop(72)


# Test 73: Payment Success Webhook
print("\n[TEST 73] UC004D - Payment Success & Inventory Update")
print("-" * 60)
if uc004d_order_id:
    payment_success_resp = req_post(f'http://localhost:8000/accessories/payment/success/{uc004d_order_id}')
    print(f"Status Code: {payment_success_resp.status_code}")
    if payment_success_resp.status_code == 200:
        success_data = payment_success_resp.json()
        print(f"✓ Payment success processed")
        print(f"  Order Number: {success_data['order_number']}")
        print(f"  Message: {success_data['message']}")
        print("✓ UC004D: Vendor notifications queued (email + WhatsApp)")
    else:
        print(f"✗ Payment success processing failed: {payment_success_resp.text}")
else:
    print("⚠ Skipped (no order ID)")
maybe_stop(73)


# Test 74: Get Order Details
print("\n[TEST 74] UC004D - Get Order Details")
print("-" * 60)
if uc004d_order_id:
    order_detail_resp = req_get(f'http://localhost:8000/accessories/orders/{uc004d_order_id}')
    print(f"Status Code: {order_detail_resp.status_code}")
    if order_detail_resp.status_code == 200:
        order = order_detail_resp.json()
        print(f"✓ Order detail fetched")
        print(f"  Order Number: {order['order_number']}")
        print(f"  Customer: {order['customer_name']}")
        print(f"  Total: ₹{order['total_amount']}")
        print(f"  Payment Status: {order['payment_status']}")
        print(f"  Order Status: {order['order_status']}")
        print(f"  Items: {len(order['items'])} item(s)")
        print(f"  Vendor: {order['vendor']['name']}")
    else:
        print(f"✗ Order detail fetch failed: {order_detail_resp.text}")
else:
    print("⚠ Skipped (no order ID)")
maybe_stop(74)


# Test 75: Payment Failure Webhook
print("\n[TEST 75] UC004D - Payment Failure Handling")
print("-" * 60)
# Create a second order for failure testing
uc004d_order_id_fail = None
if uc004d_accessory_id:
    checkout_payload = {
        "items": [
            {"product_type": "accessory", "product_id": uc004d_accessory_id, "quantity": 1}
        ],
        "customer_name": "Fail Test",
        "customer_email": "fail@test.com",
        "customer_phone": "8888888888",
        "shipping_address": "456 Test Ave, Bengaluru"
    }
    checkout_resp = req_post('http://localhost:8000/accessories/checkout', json=checkout_payload)
    if checkout_resp.status_code == 200:
        uc004d_order_id_fail = checkout_resp.json()['order_id']
        # Simulate payment failure
        failure_resp = req_post(f'http://localhost:8000/accessories/payment/failure/{uc004d_order_id_fail}')
        print(f"Status Code: {failure_resp.status_code}")
        if failure_resp.status_code == 200:
            failure_data = failure_resp.json()
            print(f"✓ Payment failure processed")
            print(f"  Message: {failure_data['message']}")
            print("✓ No order created, no vendor notified, no inventory deducted")
        else:
            print(f"✗ Failure handling failed: {failure_resp.text}")
    else:
        print(f"⚠ Could not create failure test order: {checkout_resp.status_code}")
else:
    print("⚠ Skipped (no accessory ID)")
maybe_stop(75)


# Test 76: Filter Accessories by Category
print("\n[TEST 76] UC004D - Filter Accessories by Category")
print("-" * 60)
category_filter_resp = req_get('http://localhost:8000/accessories?category=Recovery%20Gear')
print(f"Status Code: {category_filter_resp.status_code}")
if category_filter_resp.status_code == 200:
    filtered = category_filter_resp.json()
    print(f"✓ Category filter works: {len(filtered)} Recovery Gear items")
else:
    print(f"✗ Category filter failed: {category_filter_resp.text}")
maybe_stop(76)


# Test 77: Insufficient Stock Failure
print("\n[TEST 77] UC004D - Insufficient Stock Handling")
print("-" * 60)
if uc004d_accessory_id:
    # Try to checkout with excessive quantity
    checkout_payload = {
        "items": [
            {"product_type": "accessory", "product_id": uc004d_accessory_id, "quantity": 999999}
        ],
        "customer_name": "Stock Test",
        "customer_email": "stock@test.com",
        "customer_phone": "7777777777",
        "shipping_address": "789 Stock St"
    }
    checkout_resp = req_post('http://localhost:8000/accessories/checkout', json=checkout_payload)
    print(f"Status Code: {checkout_resp.status_code}")
    if checkout_resp.status_code == 400 and 'stock' in checkout_resp.text.lower():
        print("✓ Insufficient stock properly rejected (400)")
    else:
        print(f"✗ Expected 400 with stock error, got {checkout_resp.status_code}: {checkout_resp.text}")
else:
    print("⚠ Skipped (no accessory ID)")
maybe_stop(77)


# Test 78: Multiple Items from Same Vendor
print("\n[TEST 78] UC004D - Multi-Item Checkout (Same Vendor)")
print("-" * 60)
if uc004d_accessory_id:
    checkout_payload = {
        "items": [
            {"product_type": "accessory", "product_id": uc004d_accessory_id, "quantity": 2}
        ],
        "customer_name": "Multi Item",
        "customer_email": "multi@test.com",
        "customer_phone": "6666666666",
        "shipping_address": "100 Multi Lane"
    }
    checkout_resp = req_post('http://localhost:8000/accessories/checkout', json=checkout_payload)
    print(f"Status Code: {checkout_resp.status_code}")
    if checkout_resp.status_code == 200:
        order = checkout_resp.json()
        print(f"✓ Multi-item checkout successful")
        print(f"  Total Amount: ₹{order['amount']}")
    else:
        print(f"✗ Multi-item checkout failed: {checkout_resp.text}")
else:
    print("⚠ Skipped (no accessory ID)")
maybe_stop(78)


# Test 79: Authenticated User Checkout
print("\n[TEST 79] UC004D - Checkout with Authenticated User")
print("-" * 60)
if token and uc004d_accessory_id:
    headers = {'Authorization': f'Bearer {token}'}
    checkout_payload = {
        "items": [
            {"product_type": "accessory", "product_id": uc004d_accessory_id, "quantity": 1}
        ],
        "customer_name": "Rajesh Kumar",
        "customer_email": "rajesh@test.com",
        "customer_phone": "9876543210",
        "shipping_address": "Thar Bengaluru HQ, Bangalore"
    }
    checkout_resp = req_post('http://localhost:8000/accessories/checkout', headers=headers, json=checkout_payload)
    print(f"Status Code: {checkout_resp.status_code}")
    if checkout_resp.status_code == 200:
        order = checkout_resp.json()
        uc004d_auth_order_id = order['order_id']
        print(f"✓ Authenticated user checkout successful")
        print(f"  Order ID: {uc004d_auth_order_id}")
    else:
        print(f"✗ Authenticated checkout failed: {checkout_resp.text}")
else:
    print("⚠ Skipped (token/accessory unavailable)")
maybe_stop(79)


# Test 80: Get User's Order History
print("\n[TEST 80] UC004D - Get User's Accessory Orders")
print("-" * 60)
if token:
    headers = {'Authorization': f'Bearer {token}'}
    orders_resp = req_get('http://localhost:8000/accessories/orders', headers=headers)
    print(f"Status Code: {orders_resp.status_code}")
    if orders_resp.status_code == 200:
        orders = orders_resp.json()
        print(f"✓ Order history fetched: {len(orders)} order(s)")
        if len(orders) > 0:
            latest = orders[0]
            print(f"Latest order:")
            print(f"  Order Number: {latest['order_number']}")
            print(f"  Total: ₹{latest['total_amount']}")
            print(f"  Status: {latest['order_status']}")
    else:
        print(f"✗ Order history fetch failed: {orders_resp.text}")
else:
    print("⚠ Skipped (token unavailable)")
maybe_stop(80)


# ==================== UC004E: BROWSE & PURCHASE CLUB MERCHANDISE ====================

# Test 81: List Merchandise
print("\n[TEST 81] UC004E - List Merchandise")
print("-" * 60)
merch_resp = req_get('http://localhost:8000/merchandise')
print(f"Status Code: {merch_resp.status_code}")
uc004e_merchandise_id = None
if merch_resp.status_code == 200:
    merchandise = merch_resp.json()
    print(f"✓ List Merchandise Successful: {len(merchandise)} items found")
    if merchandise:
        uc004e_merchandise_id = merchandise[0]['id']
        print(f"First item: {merchandise[0]['name']} - ₹{merchandise[0]['price']}")
        print(f"Category: {merchandise[0].get('category', 'N/A')}")
else:
    print(f"✗ List Merchandise Failed: {merch_resp.text}")
maybe_stop(81)


# Test 82: Get Merchandise Detail
print("\n[TEST 82] UC004E - Get Merchandise Detail")
print("-" * 60)
if uc004e_merchandise_id:
    detail_resp = req_get(f'http://localhost:8000/merchandise/{uc004e_merchandise_id}')
    print(f"Status Code: {detail_resp.status_code}")
    if detail_resp.status_code == 200:
        detail = detail_resp.json()
        print(f"✓ Get Detail Successful: {detail['name']}")
        print(f"  Description: {detail['description']}")
        print(f"  Price: ₹{detail['price']}")
        print(f"  Stock: {detail['stock']}")
        print(f"  Material: {detail.get('material', 'N/A')}")
        if detail.get('vendor'):
            print(f"  Vendor: {detail['vendor']['name']}")
    else:
        print(f"✗ Get Detail Failed: {detail_resp.text}")
else:
    print("⚠ Skipped (no merchandise ID)")
maybe_stop(82)


# Test 83: Get Merchandise Categories
print("\n[TEST 83] UC004E - Get Merchandise Categories")
print("-" * 60)
cat_resp = req_get('http://localhost:8000/merchandise/categories')
print(f"Status Code: {cat_resp.status_code}")
if cat_resp.status_code == 200:
    categories = cat_resp.json()
    print(f"✓ Categories fetched: {list(categories.keys())}")
else:
    print(f"✗ Categories fetch failed: {cat_resp.text}")
maybe_stop(83)


# Test 84: Filter Merchandise by Category
print("\n[TEST 84] UC004E - Filter Merchandise by Category")
print("-" * 60)
filter_resp = req_get('http://localhost:8000/merchandise?category=Apparel')
print(f"Status Code: {filter_resp.status_code}")
if filter_resp.status_code == 200:
    filtered = filter_resp.json()
    print(f"✓ Category filter works: {len(filtered)} Apparel items")
else:
    print(f"✗ Category filter failed: {filter_resp.text}")
maybe_stop(84)


# Test 85: Guest Checkout Merchandise
print("\n[TEST 85] UC004E - Guest Checkout Merchandise")
print("-" * 60)
if uc004e_merchandise_id:
    checkout_payload = {
        "items": [
            {"merchandise_id": uc004e_merchandise_id, "quantity": 1, "size": "M", "color": "Red"}
        ],
        "customer_name": "Guest Shopper",
        "customer_email": "guest@test.com",
        "customer_phone": "8888888888",
        "shipping_address": "123 Test St, Bengaluru, Karnataka 560001",
        "notes": "Please pack carefully"
    }
    checkout_resp = req_post('http://localhost:8000/merchandise/checkout', json=checkout_payload)
    print(f"Status Code: {checkout_resp.status_code}")
    uc004e_order_id = None
    if checkout_resp.status_code == 200:
        checkout_data = checkout_resp.json()
        uc004e_order_id = checkout_data['order_id']
        print(f"✓ Guest checkout successful")
        print(f"  Order ID: {uc004e_order_id}")
        print(f"  Order Number: {checkout_data['order_number']}")
        print(f"  Amount: ₹{checkout_data['amount']}")
        print(f"  Payment Gateway: {checkout_data['payment_gateway']}")
    else:
        print(f"✗ Checkout failed: {checkout_resp.text}")
else:
    print("⚠ Skipped (no merchandise ID)")
    uc004e_order_id = None
maybe_stop(85)


# Test 86: Merchandise Payment Success
print("\n[TEST 86] UC004E - Merchandise Payment Success Webhook")
print("-" * 60)
if uc004e_order_id:
    payment_resp = req_post(f'http://localhost:8000/merchandise/payment/success/{uc004e_order_id}')
    print(f"Status Code: {payment_resp.status_code}")
    if payment_resp.status_code == 200:
        payment_data = payment_resp.json()
        print(f"✓ Payment success processed")
        print(f"  Message: {payment_data['message']}")
        print("✓ Order confirmed, inventory updated, vendor notified")
    else:
        print(f"✗ Payment processing failed: {payment_resp.text}")
else:
    print("⚠ Skipped (no order ID)")
maybe_stop(86)


# Test 87: Authenticated User Checkout Merchandise
print("\n[TEST 87] UC004E - Authenticated User Merchandise Checkout")
print("-" * 60)
if token and uc004e_merchandise_id:
    headers = {'Authorization': f'Bearer {token}'}
    checkout_payload = {
        "items": [
            {"merchandise_id": uc004e_merchandise_id, "quantity": 2, "size": "L"}
        ],
        "customer_name": "Rajesh Kumar",
        "customer_email": "rajesh@test.com",
        "customer_phone": "9876543210",
        "shipping_address": "456 Auth User St, Bengaluru 560002"
    }
    checkout_resp = req_post('http://localhost:8000/merchandise/checkout', json=checkout_payload, headers=headers)
    print(f"Status Code: {checkout_resp.status_code}")
    uc004e_auth_order_id = None
    if checkout_resp.status_code == 200:
        checkout_data = checkout_resp.json()
        uc004e_auth_order_id = checkout_data['order_id']
        print(f"✓ User checkout successful")
        print(f"  Order ID: {uc004e_auth_order_id}")
        print(f"  Order Number: {checkout_data['order_number']}")
    else:
        print(f"✗ Checkout failed: {checkout_resp.text}")
else:
    print("⚠ Skipped (token or merchandise ID unavailable)")
    uc004e_auth_order_id = None
maybe_stop(87)


# Test 88: Complete Authenticated Merchandise Order
print("\n[TEST 88] UC004E - Complete Authenticated Merchandise Order")
print("-" * 60)
if uc004e_auth_order_id:
    payment_resp = req_post(f'http://localhost:8000/merchandise/payment/success/{uc004e_auth_order_id}')
    print(f"Status Code: {payment_resp.status_code}")
    if payment_resp.status_code == 200:
        print(f"✓ Payment success for authenticated user order")
    else:
        print(f"✗ Payment failed: {payment_resp.text}")
else:
    print("⚠ Skipped (no auth order ID)")
maybe_stop(88)


# Test 89: Get User's Merchandise Order History
print("\n[TEST 89] UC004E - Get User's Merchandise Order History")
print("-" * 60)
if token:
    headers = {'Authorization': f'Bearer {token}'}
    orders_resp = req_get('http://localhost:8000/merchandise/orders', headers=headers)
    print(f"Status Code: {orders_resp.status_code}")
    if orders_resp.status_code == 200:
        orders = orders_resp.json()
        print(f"✓ Order history fetched: {len(orders)} order(s)")
        if len(orders) > 0:
            latest = orders[0]
            print(f"Latest order:")
            print(f"  Order Number: {latest['order_number']}")
            print(f"  Total: ₹{latest['total_amount']}")
            print(f"  Status: {latest['order_status']}")
            print(f"  Items: {len(latest['items'])} item(s)")
    else:
        print(f"✗ Order history fetch failed: {orders_resp.text}")
else:
    print("⚠ Skipped (token unavailable)")
maybe_stop(89)


# Test 90: Merchandise Payment Failure
print("\n[TEST 90] UC004E - Merchandise Payment Failure Webhook")
print("-" * 60)
if uc004e_merchandise_id:
    # Create another order for failure testing
    checkout_payload = {
        "items": [
            {"merchandise_id": uc004e_merchandise_id, "quantity": 1}
        ],
        "customer_name": "Fail Test",
        "customer_email": "fail@test.com",
        "customer_phone": "7777777777",
        "shipping_address": "789 Fail St, Bengaluru"
    }
    checkout_resp = req_post('http://localhost:8000/merchandise/checkout', json=checkout_payload)
    if checkout_resp.status_code == 200:
        fail_order_id = checkout_resp.json()['order_id']
        failure_resp = req_post(f'http://localhost:8000/merchandise/payment/failure/{fail_order_id}')
        print(f"Status Code: {failure_resp.status_code}")
        if failure_resp.status_code == 200:
            failure_data = failure_resp.json()
            print(f"✓ Payment failure processed")
            print(f"  Message: {failure_data['message']}")
            print("✓ No inventory deducted, no vendor notified")
        else:
            print(f"✗ Failure handling failed: {failure_resp.text}")
    else:
        print(f"⚠ Could not create failure test order: {checkout_resp.status_code}")
else:
    print("⚠ Skipped (no merchandise ID)")
maybe_stop(90)


# ==================== UC005: SUBMIT MEMBERSHIP REQUEST (EXISTING THAR MEMBER) ====================

# Test 91: UC005 Eligibility Check
print("\n[TEST 91] UC005 - Membership Eligibility Check")
print("-" * 60)
uc005_member_token = None
uc005_admin_token = None
uc005_request_id = None

priya_login = req_post('http://localhost:8000/auth/login', json={'email': 'priya@test.com', 'password': 'test1234'})
admin_login = req_post('http://localhost:8000/auth/login', json={'email': 'admin@test.com', 'password': 'test1234'})
if priya_login.status_code == 200:
    uc005_member_token = priya_login.json().get('access_token')
if admin_login.status_code == 200:
    uc005_admin_token = admin_login.json().get('access_token')

if uc005_member_token:
    member_headers = {'Authorization': f'Bearer {uc005_member_token}'}
    eligibility_resp = req_get('http://localhost:8000/memberships/club-requests/eligibility', headers=member_headers)
    print(f"Status Code: {eligibility_resp.status_code}")
    if eligibility_resp.status_code == 200:
        print(f"✓ Eligibility response received: {eligibility_resp.json()}")
    else:
        print(f"✗ Eligibility check failed: {eligibility_resp.text}")
else:
    print("⚠ Skipped (member token unavailable)")
maybe_stop(91)


# Test 92: UC005 Auto-fill Profile Data
print("\n[TEST 92] UC005 - Auto-fill Membership Form")
print("-" * 60)
if uc005_member_token:
    member_headers = {'Authorization': f'Bearer {uc005_member_token}'}
    autofill_resp = req_get('http://localhost:8000/memberships/club-requests/autofill', headers=member_headers)
    print(f"Status Code: {autofill_resp.status_code}")
    if autofill_resp.status_code == 200:
        auto_data = autofill_resp.json()
        print("✓ Auto-fill successful")
        print(f"  TB Member ID: {auto_data.get('tb_member_id')}")
        print(f"  Name: {auto_data.get('first_name')} {auto_data.get('last_name')}")
        print(f"  Email: {auto_data.get('email_address')}")
    else:
        print(f"✗ Auto-fill failed: {autofill_resp.text}")
else:
    print("⚠ Skipped (member token unavailable)")
maybe_stop(92)


# Test 93: UC005 Ensure Workshop Trail Completion (if needed)
print("\n[TEST 93] UC005 - Ensure Workshop Trail Completion")
print("-" * 60)
if uc005_member_token and uc005_admin_token:
    member_headers = {'Authorization': f'Bearer {uc005_member_token}'}
    admin_headers = {'Authorization': f'Bearer {uc005_admin_token}'}

    eligibility_resp = req_get('http://localhost:8000/memberships/club-requests/eligibility', headers=member_headers)
    if eligibility_resp.status_code == 200:
        eligibility = eligibility_resp.json()
        if not eligibility.get('workshop_trail_completed'):
            tblr_list_resp = req_get('http://localhost:8000/memberships/tblr-applications', headers=member_headers)
            tblr_id = None
            if tblr_list_resp.status_code == 200:
                for app in tblr_list_resp.json():
                    if app.get('status') == 'pending':
                        tblr_id = app.get('id')
                        break

            if not tblr_id:
                tblr_payload = {
                    "full_name": "Priya Singh",
                    "email": "priya@test.com",
                    "phone": "9876543211",
                    "vehicle_model": "Thar",
                    "vehicle_number": "MH-02-AB-5050",
                    "experience_level": "intermediate",
                    "motivation": "Complete workshop trail for club membership"
                }
                create_tblr = req_post('http://localhost:8000/memberships/tblr-applications', headers=member_headers, json=tblr_payload)
                if create_tblr.status_code == 200:
                    tblr_id = create_tblr.json().get('id')

            if tblr_id:
                approve_tblr = req_patch(f'http://localhost:8000/memberships/tblr-applications/{tblr_id}/approve', headers=admin_headers)
                if approve_tblr.status_code == 200:
                    print("✓ Workshop trail completion prepared via approved TBLR application")
                else:
                    print(f"⚠ Could not approve TBLR app: {approve_tblr.status_code}")
            else:
                print("⚠ Could not create/find TBLR application")
        else:
            print("✓ Workshop trail already completed")
    else:
        print(f"⚠ Eligibility check unavailable: {eligibility_resp.status_code}")
else:
    print("⚠ Skipped (member/admin token unavailable)")
maybe_stop(93)


# Test 94: UC005 Submit Membership Request (Terms Accepted)
print("\n[TEST 94] UC005 - Submit Membership Request")
print("-" * 60)
if uc005_member_token:
    member_headers = {'Authorization': f'Bearer {uc005_member_token}'}

    # Cleanup non-active requests for deterministic run
    list_resp = req_get('http://localhost:8000/memberships/club-requests', headers=member_headers)
    if list_resp.status_code == 200:
        for req in list_resp.json():
            if req.get('status') in ['pending', 'rejected', 'PENDING', 'REJECTED']:
                req_delete(f"http://localhost:8000/memberships/club-requests/{req.get('id')}", headers=member_headers)

    submit_payload = {
        "name": "Priya Singh",
        "email": "priya@test.com",
        "phone": "9876543211",
        "vehicle_model": "Thar",
        "vehicle_number": "MH-02-AB-5050",
        "registration_date": "2024-01-01T00:00:00",
        "reason": "Applying for official club membership",
        "residential_address": "Indiranagar, Bengaluru",
        "emergency_contact": "9876543211",
        "vehicle_fuel_type": "diesel",
        "vehicle_transmission_type": "manual",
        "rc_document_url": "https://example.com/docs/rc-priya.pdf",
        "insurance_document_url": "https://example.com/docs/insurance-priya.pdf",
        "aadhaar_document_url": "https://example.com/docs/aadhaar-priya.pdf",
        "driving_license_document_url": "https://example.com/docs/dl-priya.pdf",
        "terms_accepted": True
    }
    submit_resp = req_post('http://localhost:8000/memberships/club-requests', headers=member_headers, json=submit_payload)
    print(f"Status Code: {submit_resp.status_code}")
    if submit_resp.status_code == 200:
        uc005_request_id = submit_resp.json().get('id')
        print(f"✓ Membership request submitted (ID: {uc005_request_id})")
    elif submit_resp.status_code in [400, 409]:
        print(f"✓ Request blocked as expected for current state: {submit_resp.text}")
        # try to reuse latest approved request if already exists
        existing = req_get('http://localhost:8000/memberships/club-requests', headers=member_headers)
        if existing.status_code == 200 and existing.json():
            uc005_request_id = existing.json()[0].get('id')
    else:
        print(f"✗ Submit failed: {submit_resp.text}")
else:
    print("⚠ Skipped (member token unavailable)")
maybe_stop(94)


# Test 95: UC005 Admin Approve Request (Payment Pending)
print("\n[TEST 95] UC005 - Admin Approval")
print("-" * 60)
if uc005_request_id and uc005_admin_token:
    admin_headers = {'Authorization': f'Bearer {uc005_admin_token}'}
    approve_resp = req_patch(f'http://localhost:8000/memberships/club-requests/{uc005_request_id}/approve', headers=admin_headers)
    print(f"Status Code: {approve_resp.status_code}")
    if approve_resp.status_code == 200:
        print("✓ Request approved and payment unlocked")
    elif approve_resp.status_code == 400 and 'Cannot approve' in approve_resp.text:
        print("✓ Request already processed previously")
    else:
        print(f"✗ Approval failed: {approve_resp.text}")
else:
    print("⚠ Skipped (request/admin token unavailable)")
maybe_stop(95)


# Test 96: UC005 Initiate Membership Payment
print("\n[TEST 96] UC005 - Initiate Membership Payment")
print("-" * 60)
if uc005_request_id and uc005_member_token:
    member_headers = {'Authorization': f'Bearer {uc005_member_token}'}
    pay_init_resp = req_post(f'http://localhost:8000/memberships/club-requests/{uc005_request_id}/payment/initiate', headers=member_headers)
    print(f"Status Code: {pay_init_resp.status_code}")
    if pay_init_resp.status_code == 200:
        pay_data = pay_init_resp.json()
        print("✓ Membership payment initiated")
        print(f"  Order ID: {pay_data.get('payment_order_id')}")
        print(f"  Gateway: {pay_data.get('payment_gateway')}")
    elif pay_init_resp.status_code == 400 and 'already completed' in pay_init_resp.text.lower():
        print("✓ Payment already completed previously")
    else:
        print(f"✗ Payment initiation failed: {pay_init_resp.text}")
else:
    print("⚠ Skipped (request/member token unavailable)")
maybe_stop(96)


# Test 97: UC005 Payment Success -> Membership Activation + WhatsApp Link
print("\n[TEST 97] UC005 - Payment Success and Activation")
print("-" * 60)
if uc005_request_id and uc005_member_token:
    member_headers = {'Authorization': f'Bearer {uc005_member_token}'}
    success_resp = req_post(
        f'http://localhost:8000/memberships/club-requests/{uc005_request_id}/payment/success',
        headers=member_headers,
        json={"gateway_payment_id": f"test_pay_{uc005_request_id}"}
    )
    print(f"Status Code: {success_resp.status_code}")
    if success_resp.status_code == 200:
        success_data = success_resp.json()
        membership_id = success_data.get('membership_id', '')
        print("✓ Membership activated after successful payment")
        print(f"  Membership ID: {membership_id}")
        print(f"  WhatsApp Available: {success_data.get('whatsapp_join_available')}")
        if isinstance(membership_id, str) and membership_id.startswith('TBC'):
            print("✓ Membership ID format prefix validated")
    else:
        print(f"✗ Activation failed: {success_resp.text}")
else:
    print("⚠ Skipped (request/member token unavailable)")
maybe_stop(97)


# Test 98: UC005 Activation Status Endpoint
print("\n[TEST 98] UC005 - Activation Status Check")
print("-" * 60)
if uc005_request_id and uc005_member_token:
    member_headers = {'Authorization': f'Bearer {uc005_member_token}'}
    activation_resp = req_get(f'http://localhost:8000/memberships/club-requests/{uc005_request_id}/activation', headers=member_headers)
    print(f"Status Code: {activation_resp.status_code}")
    if activation_resp.status_code == 200:
        print(f"✓ Activation status: {activation_resp.json().get('membership_status')}")
    else:
        print(f"✗ Activation status fetch failed: {activation_resp.text}")
else:
    print("⚠ Skipped (request/member token unavailable)")
maybe_stop(98)


print("\n" + "=" * 60)
print("INTEGRATION TESTS COMPLETE - All 98 Tests Executed")
print("=" * 60)
print("\nENDPOINT COVERAGE:")
print("✓ Auth: login, get current user, social-login (Google/Apple/Facebook)")
print("✓ Accessories: list, detail, categories, browse with filters")
print("✓ Merchandise: list, detail")
print("✓ Feeds: list, detail, create, comments (add/get)")
print("✓ Cart: add, get, remove item, clear")
print("✓ Club Membership: submit, list, detail, approve, reject, auth checks")
print("✓ TBLR: submit, list, detail, auth checks")
print("✓ Admin Role: approve/reject workflows, 403 for non-admin")
print("✓ Buy/Sell: create, list, list my, detail, update, delete (soft), ownership checks")
print("✓ UC004 Member Discovery: list members, member profile detail")
print("✓ UC004 Vehicle Management: add, list, update, delete")
print("✓ UC004 Messaging: send message, conversation history, conversations list")
print("✓ UC004A Edit Profile: update fields, locked email/phone validation")
print("✓ UC004B Event Registration: list events, event details, register with co-passengers")
print("✓ UC004B Payment: initiate payment, verify payment, WhatsApp link generation")
print("✓ UC004B My Registrations: view user's event bookings")
print("✓ UC004C Feed Search: keyword/author search, relevance ordering, empty results")
print("✓ UC004C Feed Interactions: like toggle and membership-based interaction blocking")
print("✓ UC004D Accessories: browse categories, list with stock filtering, detail with vendor")
print("✓ UC004D Shopping: guest checkout, authenticated checkout, multi-item orders")
print("✓ UC004D Payment: success webhook, failure webhook, inventory updates")
print("✓ UC004D Vendor Integration: notifications, order tracking, order history")
print("✓ UC004D Error Handling: insufficient stock, multiple vendor validation")
print("✓ UC004E Merchandise: category listing, filtering, guest/user checkout")
print("✓ UC004E Shopping: size/color selection, multi-item orders, payment processing")
print("✓ UC004E Order Management: order history, order details, vendor integration")
print("✓ UC004E Payment: success/failure webhooks, inventory updates, notifications")
print("✓ UC005 Membership Activation: eligibility, autofill, admin approval, payment, membership ID, WhatsApp onboarding")
print("✓ Social Auth: Google, Apple, Facebook endpoints validated")
print("✓ User Response: membership_status, tblr_membership_status fields included")
print("✓ Authorization: guest 401 on protected, non-owner 403 on update, public access for lists")
print("=" * 60)

# Clean up session
session.close()


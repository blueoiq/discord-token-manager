import requests
import json
import time
import os
import base64
from datetime import datetime

TOKEN = input("Enter your Discord token: ")
HEADERS = {"Authorization": TOKEN}

# Cache for API responses
CACHE = {}
CACHE_EXPIRY = 300  # 5 minutes

def get_cached(endpoint):
    now = time.time()
    if endpoint in CACHE and now - CACHE[endpoint]['timestamp'] < CACHE_EXPIRY:
        return CACHE[endpoint]['data']
    
    r = requests.get(endpoint, headers=HEADERS)
    if r.status_code == 200:
        data = r.json()
        CACHE[endpoint] = {'data': data, 'timestamp': now}
        return data
    return None

def get_user_info():
    user = get_cached("https://discord.com/api/users/@me")
    if user:
        print(f"\nUser: {user['username']}#{user['discriminator']} (ID: {user['id']})")
        print(f"Email: {user.get('email', 'N/A')}")
        print(f"Phone: {user.get('phone', 'N/A')}")
        print(f"2FA: {user.get('mfa_enabled', 'No')}")
        print(f"Verified: {user.get('verified', 'No')}")
        print(f"Accent: {user.get('accent_color', 'N/A')}")
        print(f"Bio: {user.get('bio', 'None')}")
        print(f"Premium: {user.get('premium_type', 'None')}")
        print(f"Flags: {user.get('flags', 'None')}")
        
        # Fixed timestamp calculation
        try:
            # Discord snowflake ID timestamp extraction
            timestamp = ((int(user['id']) >> 22) + 1420070400000) / 1000  # Convert to seconds
            created_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
            print(f"Created: {created_date}")
        except (ValueError, OSError) as e:
            print(f"Created: Unable to calculate ({str(e)})")
    else:
        print("Failed to fetch user")

def get_guilds():
    return get_cached("https://discord.com/api/users/@me/guilds") or []

def list_guilds():
    guilds = get_guilds()
    print(f"\n{len(guilds)} Servers:")
    for i, g in enumerate(guilds):
        owner = "Owner" if g.get('owner') else "Member"
        print(f"{i+1}. {g['name']} (ID: {g['id']}) - {owner}")
    return guilds

def get_guild_info(guild_id):
    guild = get_cached(f"https://discord.com/api/guilds/{guild_id}")
    if guild:
        print(f"\nGuild: {guild['name']} (ID: {guild['id']})")
        print(f"Owner: {guild['owner_id']}")
        print(f"Region: {guild.get('region', 'N/A')}")
        print(f"Members: {guild.get('member_count', 'N/A')}")
        print(f"Verification: {guild.get('verification_level', 'N/A')}")
        print(f"Features: {', '.join(guild.get('features', []))}")
        print(f"Boosts: {guild.get('premium_subscription_count', 0)}")
        return guild
    return None

def list_channels(guild_id):
    channels = get_cached(f"https://discord.com/api/guilds/{guild_id}/channels")
    if channels:
        print(f"\nChannels in {guild_id}:")
        text_channels = [ch for ch in channels if ch['type'] == 0]
        voice_channels = [ch for ch in channels if ch['type'] == 2]
        
        print("\nText Channels:")
        for i, c in enumerate(text_channels):
            nsfw = "NSFW" if c.get('nsfw') else ""
            print(f"{i+1}. #{c['name']} (ID: {c['id']}) {nsfw}")
        
        print("\nVoice Channels:")
        for i, c in enumerate(voice_channels):
            print(f"{i+1}. {c['name']} (ID: {c['id']}) - {c.get('user_limit', 'No limit')} users")
        return channels
    return []

def get_channel_messages(channel_id, limit=50):
    messages = get_cached(f"https://discord.com/api/channels/{channel_id}/messages?limit={limit}")
    if messages:
        print(f"\nLast {len(messages)} messages in {channel_id}:")
        for msg in messages:
            author = msg['author']
            print(f"[{msg['timestamp'][:10]}] {author['username']}#{author['discriminator']}: {msg['content'][:100]}...")
        return messages
    return []

def get_guild_members(guild_id, limit=100):
    members = get_cached(f"https://discord.com/api/guilds/{guild_id}/members?limit={limit}")
    if members:
        print(f"\n{len(members)} members in {guild_id}:")
        for member in members:
            user = member['user']
            roles = ', '.join([f"@{r}" for r in member.get('roles', [])[:3]])
            print(f"{user['username']}#{user['discriminator']} (ID: {user['id']}) - Roles: {roles}")
        return members
    return []

def create_webhook(channel_id, name="TestHook", avatar=None):
    payload = {"name": name}
    if avatar:
        payload["avatar"] = avatar
        
    r = requests.post(f"https://discord.com/api/channels/{channel_id}/webhooks", headers=HEADERS, json=payload)
    if r.status_code == 200:
        hook = r.json()
        print(f"Webhook created: https://discord.com/api/webhooks/{hook['id']}/{hook['token']}")
        return hook
    else:
        print("Failed to create webhook:", r.json())
    return None

def send_webhook_message(webhook_url, content, username=None, avatar_url=None):
    payload = {"content": content}
    if username:
        payload["username"] = username
    if avatar_url:
        payload["avatar_url"] = avatar_url
    
    r = requests.post(webhook_url, json=payload)
    if r.status_code == 204:
        print("Webhook message sent!")
    else:
        print("Webhook send failed:", r.json())

def send_message(channel_id, content, embed=None):
    payload = {"content": content}
    if embed:
        payload["embeds"] = [embed]
    
    r = requests.post(f"https://discord.com/api/channels/{channel_id}/messages", headers=HEADERS, json=payload)
    if r.status_code == 200:
        print("Message sent!")
        return r.json()
    else:
        print("Send failed:", r.json())
    return None

def create_embed(title, description=None, color=0x00AE86):
    embed = {"title": title, "color": color}
    if description:
        embed["description"] = description
    return embed

def ban_user(guild_id, user_id, reason="", delete_message_days=0):
    payload = {"delete_message_days": delete_message_days, "reason": reason}
    r = requests.put(f"https://discord.com/api/guilds/{guild_id}/bans/{user_id}", headers=HEADERS, json=payload)
    if r.status_code == 204:
        print("User banned!")
    else:
        print("Ban failed:", r.json())

def kick_user(guild_id, user_id, reason=""):
    payload = {"reason": reason}
    r = requests.delete(f"https://discord.com/api/guilds/{guild_id}/members/{user_id}", headers=HEADERS, json=payload)
    if r.status_code == 204:
        print("User kicked!")
    else:
        print("Kick failed:", r.json())

def get_user_relationships():
    relationships = get_cached("https://discord.com/api/users/@me/relationships")
    if relationships:
        print(f"\n{len(relationships)} relationships:")
        friends = [r for r in relationships if r['type'] == 1]
        blocked = [r for r in relationships if r['type'] == 2]
        incoming = [r for r in relationships if r['type'] == 3]
        outgoing = [r for r in relationships if r['type'] == 4]
        
        print(f"Friends ({len(friends)}):")
        for f in friends[:10]:
            print(f"  {f['user']['username']}#{f['user']['discriminator']}")
            
        print(f"Blocked ({len(blocked)}):")
        for b in blocked[:5]:
            print(f"  {b['user']['username']}#{b['user']['discriminator']}")
            
        print(f"Incoming requests ({len(incoming)}):")
        for i in incoming[:5]:
            print(f"  {i['user']['username']}#{i['user']['discriminator']}")
            
        print(f"Outgoing requests ({len(outgoing)}):")
        for o in outgoing[:5]:
            print(f"  {o['user']['username']}#{o['user']['discriminator']}")
            
        return relationships
    return []

def leave_guild(guild_id):
    r = requests.delete(f"https://discord.com/api/users/@me/guilds/{guild_id}", headers=HEADERS)
    if r.status_code == 204:
        print("Left guild successfully!")
    else:
        print("Failed to leave guild:", r.json())

def delete_message(channel_id, message_id):
    r = requests.delete(f"https://discord.com/api/channels/{channel_id}/messages/{message_id}", headers=HEADERS)
    if r.status_code == 204:
        print("Message deleted successfully!")
    else:
        print("Failed to delete message:", r.json())

def delete_channel(channel_id):
    r = requests.delete(f"https://discord.com/api/channels/{channel_id}", headers=HEADERS)
    if r.status_code == 204:
        print("Channel deleted successfully!")
    else:
        print("Failed to delete channel:", r.json())

def create_invite(channel_id, max_age=86400, max_uses=0, temporary=False):
    payload = {
        "max_age": max_age,
        "max_uses": max_uses,
        "temporary": temporary
    }
    r = requests.post(f"https://discord.com/api/channels/{channel_id}/invites", headers=HEADERS, json=payload)
    if r.status_code == 200:
        invite = r.json()
        print(f"Invite created: https://discord.gg/{invite['code']}")
        return invite
    else:
        print("Failed to create invite:", r.json())
    return None

def get_guild_roles(guild_id):
    roles = get_cached(f"https://discord.com/api/guilds/{guild_id}/roles")
    if roles:
        print(f"\nRoles in {guild_id}:")
        for role in roles:
            permissions = role.get('permissions', '0')
            print(f"{role['name']} (ID: {role['id']}) - Position: {role['position']}, Color: {role.get('color', 'None')}, Permissions: {permissions}")
        return roles
    return []

def create_role(guild_id, name="New Role", permissions=0, color=0, hoist=False, mentionable=False):
    payload = {
        "name": name,
        "permissions": str(permissions),
        "color": color,
        "hoist": hoist,
        "mentionable": mentionable
    }
    r = requests.post(f"https://discord.com/api/guilds/{guild_id}/roles", headers=HEADERS, json=payload)
    if r.status_code == 200:
        role = r.json()
        print(f"Role created: {role['name']} (ID: {role['id']})")
        return role
    else:
        print("Failed to create role:", r.json())
    return None

def add_role_to_member(guild_id, user_id, role_id):
    r = requests.put(f"https://discord.com/api/guilds/{guild_id}/members/{user_id}/roles/{role_id}", headers=HEADERS)
    if r.status_code == 204:
        print("Role added to member successfully!")
    else:
        print("Failed to add role to member:", r.json())

def remove_role_from_member(guild_id, user_id, role_id):
    r = requests.delete(f"https://discord.com/api/guilds/{guild_id}/members/{user_id}/roles/{role_id}", headers=HEADERS)
    if r.status_code == 204:
        print("Role removed from member successfully!")
    else:
        print("Failed to remove role from member:", r.json())

def get_guild_emojis(guild_id):
    emojis = get_cached(f"https://discord.com/api/guilds/{guild_id}/emojis")
    if emojis:
        print(f"\nEmojis in {guild_id}:")
        for emoji in emojis:
            animated = "Animated" if emoji.get('animated') else "Static"
            print(f"{emoji['name']} (ID: {emoji['id']}) - {animated}")
        return emojis
    return []

def get_user_dms():
    channels = get_cached("https://discord.com/api/users/@me/channels")
    if channels:
        print(f"\n{len(channels)} DM channels:")
        for channel in channels:
            if channel['type'] == 1:  # DM
                recipient = channel['recipients'][0]
                print(f"DM with {recipient['username']}#{recipient['discriminator']} (ID: {channel['id']})")
            elif channel['type'] == 3:  # Group DM
                recipients = ', '.join([f"{r['username']}#{r['discriminator']}" for r in channel['recipients'][:3]])
                print(f"Group DM with {recipients}... (ID: {channel['id']})")
        return channels
    return []

def start_typing(channel_id):
    r = requests.post(f"https://discord.com/api/channels/{channel_id}/typing", headers=HEADERS)
    if r.status_code == 204:
        print("Typing indicator sent!")
    else:
        print("Failed to send typing indicator:", r.json())

def get_guild_bans(guild_id):
    bans = get_cached(f"https://discord.com/api/guilds/{guild_id}/bans")
    if bans:
        print(f"\nBans in {guild_id}:")
        for ban in bans:
            user = ban['user']
            print(f"{user['username']}#{user['discriminator']} (ID: {user['id']}) - Reason: {ban.get('reason', 'None')}")
        return bans
    return []

def get_guild_audit_logs(guild_id, limit=50, action_type=None):
    params = {"limit": limit}
    if action_type:
        params["action_type"] = action_type
    
    r = requests.get(f"https://discord.com/api/guilds/{guild_id}/audit-logs", headers=HEADERS, params=params)
    if r.status_code == 200:
        logs = r.json()
        print(f"\nAudit logs for {guild_id}:")
        for entry in logs.get('audit_log_entries', []):
            user = logs['users'][str(entry['user_id'])]
            target_type = entry['target_type']
            action = entry['action_type']
            print(f"[{entry['id']}] {user['username']}#{user['discriminator']} - {target_type} - {action}")
        return logs
    else:
        print("Failed to get audit logs:", r.json())
    return None

def get_guild_integrations(guild_id):
    integrations = get_cached(f"https://discord.com/api/guilds/{guild_id}/integrations")
    if integrations:
        print(f"\nIntegrations in {guild_id}:")
        for integration in integrations:
            print(f"{integration['name']} (ID: {integration['id']}) - Type: {integration['type']}")
        return integrations
    return []

def get_guild_prune_count(guild_id, days=7):
    params = {"days": days}
    r = requests.get(f"https://discord.com/api/guilds/{guild_id}/prune", headers=HEADERS, params=params)
    if r.status_code == 200:
        data = r.json()
        print(f"\nPrune count for {guild_id}: {data.get('pruned', 0)} members would be pruned")
        return data
    else:
        print("Failed to get prune count:", r.json())
    return None

def begin_guild_prune(guild_id, days=7, reason=""):
    params = {"days": days}
    payload = {"reason": reason}
    r = requests.post(f"https://discord.com/api/guilds/{guild_id}/prune", headers=HEADERS, json=payload, params=params)
    if r.status_code == 200:
        data = r.json()
        print(f"Prune started for {guild_id}: {data.get('pruned', 0)} members will be pruned")
        return data
    else:
        print("Failed to start prune:", r.json())
    return None

def get_guild_vanity_url(guild_id):
    r = requests.get(f"https://discord.com/api/guilds/{guild_id}/vanity-url", headers=HEADERS)
    if r.status_code == 200:
        data = r.json()
        print(f"\nVanity URL for {guild_id}: https://discord.gg/{data['code']}")
        print(f"Uses: {data['uses']}")
        return data
    else:
        print("Failed to get vanity URL:", r.json())
    return None

def modify_guild(guild_id, name=None, region=None, verification_level=None, default_message_notifications=None):
    payload = {}
    if name:
        payload["name"] = name
    if region:
        payload["region"] = region
    if verification_level is not None:
        payload["verification_level"] = verification_level
    if default_message_notifications is not None:
        payload["default_message_notifications"] = default_message_notifications
    
    r = requests.patch(f"https://discord.com/api/guilds/{guild_id}", headers=HEADERS, json=payload)
    if r.status_code == 200:
        guild = r.json()
        print(f"Guild modified: {guild['name']}")
        return guild
    else:
        print("Failed to modify guild:", r.json())
    return None

def get_guild_widget(guild_id):
    widget = get_cached(f"https://discord.com/api/guilds/{guild_id}/widget.json")
    if widget:
        print(f"\nWidget for {guild_id}:")
        print(f"Name: {widget['name']}")
        print(f"Instant Invite: {widget.get('instant_invite', 'None')}")
        print(f"Presence Count: {widget['presence_count']}")
        print(f"Channels: {len(widget.get('channels', []))}")
        print(f"Members: {len(widget.get('members', []))}")
        return widget
    return None

def get_guild_preview(guild_id):
    preview = get_cached(f"https://discord.com/api/guilds/{guild_id}/preview")
    if preview:
        print(f"\nPreview for {guild_id}:")
        print(f"Name: {preview['name']}")
        print(f"Description: {preview.get('description', 'None')}")
        print(f"Features: {', '.join(preview.get('features', []))}")
        print(f"Member Count: {preview['approximate_member_count']}")
        print(f"Presence Count: {preview['approximate_presence_count']}")
        print(f"Emojis: {len(preview.get('emojis', []))}")
        return preview
    return None

def add_guild_member(guild_id, user_id, access_token, nick=None, roles=None, mute=False, deaf=False):
    payload = {
        "access_token": access_token
    }
    if nick:
        payload["nick"] = nick
    if roles:
        payload["roles"] = roles
    payload["mute"] = mute
    payload["deaf"] = deaf
    
    r = requests.put(f"https://discord.com/api/guilds/{guild_id}/members/{user_id}", headers=HEADERS, json=payload)
    if r.status_code == 201 or r.status_code == 204:
        print("Member added to guild successfully!")
        return True
    else:
        print("Failed to add member to guild:", r.json())
    return False

def create_guild_category(guild_id, name, permission_overwrites=None):
    payload = {
        "name": name,
        "type": 4  # Category type
    }
    if permission_overwrites:
        payload["permission_overwrites"] = permission_overwrites
    
    r = requests.post(f"https://discord.com/api/guilds/{guild_id}/channels", headers=HEADERS, json=payload)
    if r.status_code == 201:
        category = r.json()
        print(f"Category created: {category['name']} (ID: {category['id']})")
        return category
    else:
        print("Failed to create category:", r.json())
    return None

def create_text_channel(guild_id, name, parent_id=None, topic=None, nsfw=False, position=None, permission_overwrites=None):
    payload = {
        "name": name,
        "type": 0  # Text channel type
    }
    if parent_id:
        payload["parent_id"] = parent_id
    if topic:
        payload["topic"] = topic
    if nsfw:
        payload["nsfw"] = nsfw
    if position is not None:
        payload["position"] = position
    if permission_overwrites:
        payload["permission_overwrites"] = permission_overwrites
    
    r = requests.post(f"https://discord.com/api/guilds/{guild_id}/channels", headers=HEADERS, json=payload)
    if r.status_code == 201:
        channel = r.json()
        print(f"Text channel created: {channel['name']} (ID: {channel['id']})")
        return channel
    else:
        print("Failed to create text channel:", r.json())
    return None

def create_voice_channel(guild_id, name, parent_id=None, bitrate=None, user_limit=None, position=None, permission_overwrites=None):
    payload = {
        "name": name,
        "type": 2  # Voice channel type
    }
    if parent_id:
        payload["parent_id"] = parent_id
    if bitrate:
        payload["bitrate"] = bitrate
    if user_limit:
        payload["user_limit"] = user_limit
    if position is not None:
        payload["position"] = position
    if permission_overwrites:
        payload["permission_overwrites"] = permission_overwrites
    
    r = requests.post(f"https://discord.com/api/guilds/{guild_id}/channels", headers=HEADERS, json=payload)
    if r.status_code == 201:
        channel = r.json()
        print(f"Voice channel created: {channel['name']} (ID: {channel['id']})")
        return channel
    else:
        print("Failed to create voice channel:", r.json())
    return None

def edit_channel(channel_id, name=None, topic=None, position=None, nsfw=None, permission_overwrites=None):
    payload = {}
    if name:
        payload["name"] = name
    if topic is not None:
        payload["topic"] = topic
    if position is not None:
        payload["position"] = position
    if nsfw is not None:
        payload["nsfw"] = nsfw
    if permission_overwrites:
        payload["permission_overwrites"] = permission_overwrites
    
    r = requests.patch(f"https://discord.com/api/channels/{channel_id}", headers=HEADERS, json=payload)
    if r.status_code == 200:
        channel = r.json()
        print(f"Channel edited: {channel['name']} (ID: {channel['id']})")
        return channel
    else:
        print("Failed to edit channel:", r.json())
    return None

def get_guild_permissions(guild_id):
    guild = get_cached(f"https://discord.com/api/guilds/{guild_id}")
    if guild:
        print(f"\nPermissions in {guild_id}:")
        print(f"Your permissions: {guild.get('permissions', 'None')}")
        print(f"Owner: {guild.get('owner', 'No')}")
        return guild
    return None

def get_user_guild_permissions(guild_id, user_id):
    member = get_cached(f"https://discord.com/api/guilds/{guild_id}/members/{user_id}")
    if member:
        print(f"\nPermissions for user {user_id} in {guild_id}:")
        print(f"Roles: {', '.join(member.get('roles', []))}")
        print(f"Permissions: {member.get('permissions', 'None')}")
        print(f"Joined: {member.get('joined_at', 'N/A')}")
        return member
    return None

def create_guild_emoji(guild_id, name, image, roles=None):
    payload = {
        "name": name,
        "image": image
    }
    if roles:
        payload["roles"] = roles
    
    r = requests.post(f"https://discord.com/api/guilds/{guild_id}/emojis", headers=HEADERS, json=payload)
    if r.status_code == 201:
        emoji = r.json()
        print(f"Emoji created: {emoji['name']} (ID: {emoji['id']})")
        return emoji
    else:
        print("Failed to create emoji:", r.json())
    return None

def delete_guild_emoji(guild_id, emoji_id):
    r = requests.delete(f"https://discord.com/api/guilds/{guild_id}/emojis/{emoji_id}", headers=HEADERS)
    if r.status_code == 204:
        print("Emoji deleted successfully!")
        return True
    else:
        print("Failed to delete emoji:", r.json())
    return False

def get_guild_templates(guild_id):
    templates = get_cached(f"https://discord.com/api/guilds/{guild_id}/templates")
    if templates:
        print(f"\nTemplates for {guild_id}:")
        for template in templates:
            print(f"{template['name']} (Code: {template['code']})")
            print(f"Description: {template.get('description', 'None')}")
            print(f"Uses: {template['usage_count']}")
            print(f"Creator: {template['creator']['username']}#{template['creator']['discriminator']}")
        return templates
    return []

def create_guild_template(guild_id, name, description=None):
    payload = {
        "name": name
    }
    if description:
        payload["description"] = description
    
    r = requests.post(f"https://discord.com/api/guilds/{guild_id}/templates", headers=HEADERS, json=payload)
    if r.status_code == 200:
        template = r.json()
        print(f"Template created: {template['name']} (Code: {template['code']})")
        return template
    else:
        print("Failed to create template:", r.json())
    return None

def delete_guild_template(guild_id, template_code):
    r = requests.delete(f"https://discord.com/api/guilds/{guild_id}/templates/{template_code}", headers=HEADERS)
    if r.status_code == 200:
        print("Template deleted successfully!")
        return True
    else:
        print("Failed to delete template:", r.json())
    return False


def get_guild_welcome_screen(guild_id):
    welcome = get_cached(f"https://discord.com/api/guilds/{guild_id}/welcome-screen")
    if welcome:
        print(f"\nWelcome screen for {guild_id}:")
        print(f"Enabled: {welcome.get('enabled', 'No')}")
        print(f"Description: {welcome.get('description', 'None')}")
        
        for i, channel in enumerate(welcome.get('welcome_channels', [])):
            print(f"  Channel {i+1}: {channel['emoji_name']} - {channel['channel_id']}")
        return welcome
    return None

def modify_guild_welcome_screen(guild_id, enabled=None, description=None, welcome_channels=None):
    payload = {}
    if enabled is not None:
        payload["enabled"] = enabled
    if description is not None:
        payload["description"] = description
    if welcome_channels:
        payload["welcome_channels"] = welcome_channels
    
    r = requests.patch(f"https://discord.com/api/guilds/{guild_id}/welcome-screen", headers=HEADERS, json=payload)
    if r.status_code == 200:
        welcome = r.json()
        print(f"Welcome screen modified for {guild_id}")
        return welcome
    else:
        print("Failed to modify welcome screen:", r.json())
    return None

def get_guild_stickers(guild_id):
    stickers = get_cached(f"https://discord.com/api/guilds/{guild_id}/stickers")
    if stickers:
        print(f"\nStickers in {guild_id}:")
        for sticker in stickers:
            print(f"{sticker['name']} (ID: {sticker['id']}) - Format: {sticker['format_type']}")
        return stickers
    return []

def create_guild_sticker(guild_id, name, description, tags, image_data):
    payload = {
        "name": name,
        "description": description,
        "tags": tags
    }
    
    # Note: This would need multipart/form-data for actual file upload
    # Simplified for this example
    r = requests.post(f"https://discord.com/api/guilds/{guild_id}/stickers", headers=HEADERS, json=payload)
    if r.status_code == 201:
        sticker = r.json()
        print(f"Sticker created: {sticker['name']} (ID: {sticker['id']})")
        return sticker
    else:
        print("Failed to create sticker:", r.json())
    return None

def get_stage_instances(guild_id):
    instances = get_cached(f"https://discord.com/api/stage-instances")
    if instances:
        print(f"\nStage instances in {guild_id}:")
        for instance in instances:
            print(f"Channel: {instance['channel_id']} - Topic: {instance['topic']}")
            print(f"Privacy: {instance['privacy_level']}")
        return instances
    return []

def create_stage_instance(channel_id, topic, privacy_level=1):
    payload = {
        "channel_id": channel_id,
        "topic": topic,
        "privacy_level": privacy_level
    }
    
    r = requests.post(f"https://discord.com/api/stage-instances", headers=HEADERS, json=payload)
    if r.status_code == 201:
        instance = r.json()
        print(f"Stage instance created in channel {channel_id}")
        return instance
    else:
        print("Failed to create stage instance:", r.json())
    return None

def get_application_info():
    app = get_cached("https://discord.com/api/users/@me/application")
    if app:
        print(f"\nApplication Info:")
        print(f"Name: {app['name']}")
        print(f"ID: {app['id']}")
        print(f"Description: {app.get('description', 'None')}")
        print(f"Public: {app.get('bot_public', 'No')}")
        print(f"Require OAuth Grant: {app.get('bot_require_code_grant', 'No')}")
        return app
    return None

def get_connections():
    connections = get_cached("https://discord.com/api/users/@me/connections")
    if connections:
        print(f"\nConnections:")
        for conn in connections:
            print(f"{conn['type']}: {conn['name']} - {conn['id']}")
            print(f"Verified: {conn['verified']}")
            print(f"Friend Sync: {conn.get('friend_sync', 'No')}")
            print(f"Show Activity: {conn.get('show_activity', 'No')}")
        return connections
    return []

def get_voice_regions():
    regions = get_cached("https://discord.com/api/voice/regions")
    if regions:
        print(f"\nVoice Regions:")
        for region in regions:
            print(f"{region['name']} ({region['id']}) - {region['vip'] and 'VIP' or 'Standard'}")
            print(f"Optimal: {region['optimal']}")
            print(f"Deprecated: {region['deprecated']}")
            print(f"Custom: {region['custom']}")
        return regions
    return []

def menu():
    while True:
        print("\n" + "="*50)
        print("Discord Token Manager v2.0")
        print("="*50)
        print("1. User Information")
        print("2. Guild Management")
        print("3. Channel Management")
        print("4. Message Operations")
        print("5. Member Management")
        print("6. Role Management")
        print("7. Webhook Operations")
        print("8. Guild Security & Audit")
        print("9. Guild Customization")
        print("10. Advanced Operations")
        print("11. Exit")
        
        choice = input("Choose an option: ")
        
        if choice == "1":
            user_menu()
        elif choice == "2":
            guild_menu()
        elif choice == "3":
            channel_menu()
        elif choice == "4":
            message_menu()
        elif choice == "5":
            member_menu()
        elif choice == "6":
            role_menu()
        elif choice == "7":
            webhook_menu()
        elif choice == "8":
            security_menu()
        elif choice == "9":
            customization_menu()
        elif choice == "10":
            advanced_menu()
        elif choice == "11":
            print("Exiting...")
            break
        else:
            print("Invalid option, try again.")

def user_menu():
    while True:
        print("\n" + "-"*40)
        print("User Information")
        print("-"*40)
        print("1. Get User Info")
        print("2. Get Relationships")
        print("3. Get DM Channels")
        print("4. Get Connections")
        print("5. Back to Main Menu")
        
        choice = input("Choose an option: ")
        
        if choice == "1":
            get_user_info()
        elif choice == "2":
            get_user_relationships()
        elif choice == "3":
            get_user_dms()
        elif choice == "4":
            get_connections()
        elif choice == "5":
            break
        else:
            print("Invalid option, try again.")

def guild_menu():
    while True:
        print("\n" + "-"*40)
        print("Guild Management")
        print("-"*40)
        print("1. List Guilds")
        print("2. Get Guild Info")
        print("3. Leave Guild")
        print("4. Get Guild Preview")
        print("5. Get Guild Emojis")
        print("6. Get Guild Stickers")
        print("7. Get Guild Templates")
        print("8. Get Guild Welcome Screen")
        print("9. Back to Main Menu")
        
        choice = input("Choose an option: ")
        
        if choice == "1":
            list_guilds()
        elif choice == "2":
            guild_id = input("Guild ID: ")
            get_guild_info(guild_id)
        elif choice == "3":
            guild_id = input("Guild ID: ")
            confirm = input(f"Are you sure you want to leave guild {guild_id}? (y/n): ")
            if confirm.lower() == "y":
                leave_guild(guild_id)
        elif choice == "4":
            guild_id = input("Guild ID: ")
            get_guild_preview(guild_id)
        elif choice == "5":
            guild_id = input("Guild ID: ")
            get_guild_emojis(guild_id)
        elif choice == "6":
            guild_id = input("Guild ID: ")
            get_guild_stickers(guild_id)
        elif choice == "7":
            guild_id = input("Guild ID: ")
            get_guild_templates(guild_id)
        elif choice == "8":
            guild_id = input("Guild ID: ")
            get_guild_welcome_screen(guild_id)
        elif choice == "9":
            break
        else:
            print("Invalid option, try again.")


def channel_menu():
    while True:
        print("\n" + "-"*40)
        print("Channel Management")
        print("-"*40)
        print("1. List Channels in Guild")
        print("2. Create Text Channel")
        print("3. Create Voice Channel")
        print("4. Create Category")
        print("5. Edit Channel")
        print("6. Delete Channel")
        print("7. Create Invite")
        print("8. Get Channel Messages")
        print("9. Start Typing Indicator")
        print("10. Back to Main Menu")
        
        choice = input("Choose an option: ")
        
        if choice == "1":
            guild_id = input("Guild ID: ")
            list_channels(guild_id)
        elif choice == "2":
            guild_id = input("Guild ID: ")
            name = input("Channel Name: ")
            topic = input("Topic (optional): ") or None
            nsfw = input("NSFW? (y/n): ").lower() == "y"
            parent_id = input("Category ID (optional): ") or None
            create_text_channel(guild_id, name, parent_id, topic, nsfw)
        elif choice == "3":
            guild_id = input("Guild ID: ")
            name = input("Channel Name: ")
            user_limit = input("User limit (optional): ") or None
            if user_limit:
                user_limit = int(user_limit)
            bitrate = input("Bitrate (optional): ") or None
            if bitrate:
                bitrate = int(bitrate)
            parent_id = input("Category ID (optional): ") or None
            create_voice_channel(guild_id, name, parent_id, bitrate, user_limit)
        elif choice == "4":
            guild_id = input("Guild ID: ")
            name = input("Category Name: ")
            create_guild_category(guild_id, name)
        elif choice == "5":
            channel_id = input("Channel ID: ")
            name = input("New Name (optional): ") or None
            topic = input("New Topic (optional): ") or None
            position = input("New Position (optional): ") or None
            if position:
                position = int(position)
            nsfw = input("NSFW? (y/n, leave blank to keep current): ")
            if nsfw:
                nsfw = nsfw.lower() == "y"
            else:
                nsfw = None
            edit_channel(channel_id, name, topic, position, nsfw)
        elif choice == "6":
            channel_id = input("Channel ID: ")
            confirm = input(f"Are you sure you want to delete channel {channel_id}? (y/n): ")
            if confirm.lower() == "y":
                delete_channel(channel_id)
        elif choice == "7":
            channel_id = input("Channel ID: ")
            max_age = input("Max age in seconds (default 86400): ") or 86400
            max_uses = input("Max uses (0 for unlimited): ") or 0
            temporary = input("Temporary invite? (y/n): ").lower() == "y"
            create_invite(channel_id, int(max_age), int(max_uses), temporary)
        elif choice == "8":
            channel_id = input("Channel ID: ")
            limit = input("Number of messages to fetch (default 50): ") or 50
            get_channel_messages(channel_id, int(limit))
        elif choice == "9":
            channel_id = input("Channel ID: ")
            start_typing(channel_id)
        elif choice == "10":
            break
        else:
            print("Invalid option, try again.")

def message_menu():
    while True:
        print("\n" + "-"*40)
        print("Message Operations")
        print("-"*40)
        print("1. Send Message")
        print("2. Send Message with Embed")
        print("3. Delete Message")
        print("4. Get Channel Messages")
        print("5. Back to Main Menu")
        
        choice = input("Choose an option: ")
        
        if choice == "1":
            channel_id = input("Channel ID: ")
            content = input("Message Content: ")
            send_message(channel_id, content)
        elif choice == "2":
            channel_id = input("Channel ID: ")
            title = input("Embed Title: ")
            description = input("Embed Description: ")
            color = input("Embed Color (hex, default 0x00AE86): ") or "0x00AE86"
            try:
                color = int(color, 16)
            except ValueError:
                color = 0x00AE86
            content = input("Message Content (optional): ") or ""
            embed = create_embed(title, description, color)
            send_message(channel_id, content, embed)
        elif choice == "3":
            channel_id = input("Channel ID: ")
            message_id = input("Message ID: ")
            delete_message(channel_id, message_id)
        elif choice == "4":
            channel_id = input("Channel ID: ")
            limit = input("Number of messages to fetch (default 50): ") or 50
            get_channel_messages(channel_id, int(limit))
        elif choice == "5":
            break
        else:
            print("Invalid option, try again.")

def member_menu():
    while True:
        print("\n" + "-"*40)
        print("Member Management")
        print("-"*40)
        print("1. Get Guild Members")
        print("2. Get User Permissions in Guild")
        print("3. Ban User")
        print("4. Kick User")
        print("5. Add Member to Guild")
        print("6. Get Guild Bans")
        print("7. Back to Main Menu")
        
        choice = input("Choose an option: ")
        
        if choice == "1":
            guild_id = input("Guild ID: ")
            limit = input("Number of members to fetch (default 100): ") or 100
            get_guild_members(guild_id, int(limit))
        elif choice == "2":
            guild_id = input("Guild ID: ")
            user_id = input("User ID: ")
            get_user_guild_permissions(guild_id, user_id)
        elif choice == "3":
            guild_id = input("Guild ID: ")
            user_id = input("User ID: ")
            reason = input("Reason (optional): ")
            delete_days = input("Delete message days (0-7, default 0): ") or 0
            ban_user(guild_id, user_id, reason, int(delete_days))
        elif choice == "4":
            guild_id = input("Guild ID: ")
            user_id = input("User ID: ")
            reason = input("Reason (optional): ")
            kick_user(guild_id, user_id, reason)
        elif choice == "5":
            guild_id = input("Guild ID: ")
            user_id = input("User ID: ")
            access_token = input("OAuth2 Access Token: ")
            nick = input("Nickname (optional): ") or None
            roles = input("Role IDs (comma separated, optional): ")
            if roles:
                roles = [r.strip() for r in roles.split(",")]
            else:
                roles = None
            mute = input("Mute on join? (y/n): ").lower() == "y"
            deaf = input("Deafen on join? (y/n): ").lower() == "y"
            add_guild_member(guild_id, user_id, access_token, nick, roles, mute, deaf)
        elif choice == "6":
            guild_id = input("Guild ID: ")
            get_guild_bans(guild_id)
        elif choice == "7":
            break
        else:
            print("Invalid option, try again.")

def role_menu():
    while True:
        print("\n" + "-"*40)
        print("Role Management")
        print("-"*40)
        print("1. Get Guild Roles")
        print("2. Create Role")
        print("3. Add Role to Member")
        print("4. Remove Role from Member")
        print("5. Back to Main Menu")
        
        choice = input("Choose an option: ")
        
        if choice == "1":
            guild_id = input("Guild ID: ")
            get_guild_roles(guild_id)
        elif choice == "2":
            guild_id = input("Guild ID: ")
            name = input("Role Name: ")
            permissions = input("Permissions (integer, default 0): ") or 0
            color = input("Color (decimal, default 0): ") or 0
            hoist = input("Display separately? (y/n): ").lower() == "y"
            mentionable = input("Mentionable? (y/n): ").lower() == "y"
            create_role(guild_id, name, int(permissions), int(color), hoist, mentionable)
        elif choice == "3":
            guild_id = input("Guild ID: ")
            user_id = input("User ID: ")
            role_id = input("Role ID: ")
            add_role_to_member(guild_id, user_id, role_id)
        elif choice == "4":
            guild_id = input("Guild ID: ")
            user_id = input("User ID: ")
            role_id = input("Role ID: ")
            remove_role_from_member(guild_id, user_id, role_id)
        elif choice == "5":
            break
        else:
            print("Invalid option, try again.")

def webhook_menu():
    while True:
        print("\n" + "-"*40)
        print("Webhook Operations")
        print("-"*40)
        print("1. Create Webhook")
        print("2. Send Webhook Message")
        print("3. Back to Main Menu")
        
        choice = input("Choose an option: ")
        
        if choice == "1":
            channel_id = input("Channel ID: ")
            name = input("Webhook Name: ")
            avatar = input("Avatar URL (optional): ") or None
            create_webhook(channel_id, name, avatar)
        elif choice == "2":
            webhook_url = input("Webhook URL: ")
            content = input("Message Content: ")
            username = input("Username (optional): ") or None
            avatar_url = input("Avatar URL (optional): ") or None
            send_webhook_message(webhook_url, content, username, avatar_url)
        elif choice == "3":
            break
        else:
            print("Invalid option, try again.")

def security_menu():
    while True:
        print("\n" + "-"*40)
        print("Guild Security & Audit")
        print("-"*40)
        print("1. Get Guild Audit Logs")
        print("2. Get Guild Integrations")
        print("3. Get Guild Prune Count")
        print("4. Begin Guild Prune")
        print("5. Get Guild Vanity URL")
        print("6. Get Guild Widget")
        print("7. Get Guild Permissions")
        print("8. Back to Main Menu")
        
        choice = input("Choose an option: ")
        
        if choice == "1":
            guild_id = input("Guild ID: ")
            limit = input("Number of entries to fetch (default 50): ") or 50
            action_type = input("Action type (optional): ") or None
            if action_type:
                action_type = int(action_type)
            get_guild_audit_logs(guild_id, int(limit), action_type)
        elif choice == "2":
            guild_id = input("Guild ID: ")
            get_guild_integrations(guild_id)
        elif choice == "3":
            guild_id = input("Guild ID: ")
            days = input("Days of inactivity (default 7): ") or 7
            get_guild_prune_count(guild_id, int(days))
        elif choice == "4":
            guild_id = input("Guild ID: ")
            days = input("Days of inactivity (default 7): ") or 7
            reason = input("Reason (optional): ")
            begin_guild_prune(guild_id, int(days), reason)
        elif choice == "5":
            guild_id = input("Guild ID: ")
            get_guild_vanity_url(guild_id)
        elif choice == "6":
            guild_id = input("Guild ID: ")
            get_guild_widget(guild_id)
        elif choice == "7":
            guild_id = input("Guild ID: ")
            get_guild_permissions(guild_id)
        elif choice == "8":
            break
        else:
            print("Invalid option, try again.")

def customization_menu():
    while True:
        print("\n" + "-"*40)
        print("Guild Customization")
        print("-"*40)
        print("1. Modify Guild")
        print("2. Create Guild Emoji")
        print("3. Delete Guild Emoji")
        print("4. Create Guild Template")
        print("5. Delete Guild Template")
        print("6. Modify Welcome Screen")
        print("7. Create Guild Sticker")
        print("8. Create Stage Instance")
        print("9. Back to Main Menu")
        
        choice = input("Choose an option: ")
        
        if choice == "1":
            guild_id = input("Guild ID: ")
            name = input("New Name (optional): ") or None
            region = input("New Region (optional): ") or None
            verification_level = input("Verification Level (0-4, optional): ")
            if verification_level:
                verification_level = int(verification_level)
            else:
                verification_level = None
            notifications = input("Default Message Notifications (0-1, optional): ")
            if notifications:
                notifications = int(notifications)
            else:
                notifications = None
            modify_guild(guild_id, name, region, verification_level, notifications)
        elif choice == "2":
            guild_id = input("Guild ID: ")
            name = input("Emoji Name: ")
            image = input("Image (base64): ")
            roles = input("Role IDs (comma separated, optional): ")
            if roles:
                roles = [r.strip() for r in roles.split(",")]
            else:
                roles = None
            create_guild_emoji(guild_id, name, image, roles)
        elif choice == "3":
            guild_id = input("Guild ID: ")
            emoji_id = input("Emoji ID: ")
            delete_guild_emoji(guild_id, emoji_id)
        elif choice == "4":
            guild_id = input("Guild ID: ")
            name = input("Template Name: ")
            description = input("Description (optional): ") or None
            create_guild_template(guild_id, name, description)
        elif choice == "5":
            guild_id = input("Guild ID: ")
            template_code = input("Template Code: ")
            delete_guild_template(guild_id, template_code)
        elif choice == "6":
            guild_id = input("Guild ID: ")
            enabled = input("Enable welcome screen? (y/n, leave blank to keep current): ")
            if enabled:
                enabled = enabled.lower() == "y"
            else:
                enabled = None
            description = input("Description (optional): ") or None
            modify_guild_welcome_screen(guild_id, enabled, description)
        elif choice == "7":
            guild_id = input("Guild ID: ")
            name = input("Sticker Name: ")
            description = input("Description: ")
            tags = input("Tags: ")
            image_data = input("Image Data (base64): ")
            create_guild_sticker(guild_id, name, description, tags, image_data)
        elif choice == "8":
            channel_id = input("Channel ID: ")
            topic = input("Topic: ")
            privacy_level = input("Privacy Level (1-2, default 1): ") or 1
            create_stage_instance(channel_id, topic, int(privacy_level))
        elif choice == "9":
            break
        else:
            print("Invalid option, try again.")

def advanced_menu():
    while True:
        print("\n" + "-"*40)
        print("Advanced Operations")
        print("-"*40)
        print("1. Get Stage Instances")
        print("2. Get Application Info")
        print("3. Get Voice Regions")
        print("4. Back to Main Menu")
        
        choice = input("Choose an option: ")
        
        if choice == "1":
            guild_id = input("Guild ID: ")
            get_stage_instances(guild_id)
        elif choice == "2":
            get_application_info()
        elif choice == "3":
            get_voice_regions()
        elif choice == "4":
            break
        else:
            print("Invalid option, try again.")

if __name__ == "__main__":
    menu()

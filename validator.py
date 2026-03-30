"""
validator.py
Validates:
- IP addresses
- Subnet masks and CIDR notation
- Cisco config files
- Network topology (from text descriptions)
"""

import ipaddress
import re


# ─────────────────────────────────────────────
#  IP ADDRESS VALIDATION
# ─────────────────────────────────────────────

def validate_ip(ip_string):
    """
    Validate an IP address.
    Returns dict with result and details.
    """
    ip_string = ip_string.strip()

    try:
        ip = ipaddress.ip_address(ip_string)

        # Check for special/reserved ranges
        issues = []
        suggestions = []

        if ip.is_loopback:
            issues.append("This is a loopback address (127.x.x.x) — not for interface use")
        if ip.is_multicast:
            issues.append("This is a multicast address — not for interface use")
        if ip.is_unspecified:
            issues.append("This is 0.0.0.0 — not valid for interface use")
        if ip.is_link_local:
            issues.append("This is a link-local address (169.254.x.x)")
        if ip.is_private:
            suggestions.append("✅ Private IP — good for lab use")
        else:
            suggestions.append("⚠️ Public IP — use private IPs (192.168.x.x, 10.x.x.x, 172.16-31.x.x) in labs")

        return {
            "valid": True,
            "ip": str(ip),
            "version": f"IPv{ip.version}",
            "type": "private" if ip.is_private else "public",
            "issues": issues,
            "suggestions": suggestions
        }

    except ValueError:
        # Try to suggest what's wrong
        parts = ip_string.split('.')
        suggestions = []

        if len(parts) != 4:
            suggestions.append(f"IPv4 needs exactly 4 octets (e.g. 192.168.1.1), you have {len(parts)}")
        else:
            for i, part in enumerate(parts):
                try:
                    val = int(part)
                    if val < 0 or val > 255:
                        suggestions.append(f"Octet {i+1} ({part}) must be 0–255")
                except ValueError:
                    suggestions.append(f"Octet {i+1} ({part}) is not a number")

        return {
            "valid": False,
            "error": f"'{ip_string}' is not a valid IP address",
            "suggestions": suggestions
        }


# ─────────────────────────────────────────────
#  SUBNET VALIDATION
# ─────────────────────────────────────────────

def validate_subnet(network_string):
    """
    Validate a network/subnet.
    Accepts CIDR (192.168.1.0/24) or IP+mask (192.168.1.0 255.255.255.0)
    """
    network_string = network_string.strip()

    # Convert "IP MASK" format to CIDR if needed
    if ' ' in network_string:
        parts = network_string.split()
        if len(parts) == 2:
            try:
                # Convert mask to prefix length
                mask = ipaddress.IPv4Address(parts[1])
                mask_int = int(mask)
                prefix_len = bin(mask_int).count('1')
                network_string = f"{parts[0]}/{prefix_len}"
            except Exception:
                return {"valid": False, "error": f"Could not parse '{network_string}'"}

    try:
        net = ipaddress.ip_network(network_string, strict=False)

        hosts = list(net.hosts())
        total_hosts = len(hosts)

        result = {
            "valid": True,
            "network": str(net.network_address),
            "broadcast": str(net.broadcast_address),
            "netmask": str(net.netmask),
            "cidr": f"/{net.prefixlen}",
            "prefix_length": net.prefixlen,
            "total_addresses": net.num_addresses,
            "usable_hosts": total_hosts,
        }

        if total_hosts > 0:
            result["first_host"] = str(hosts[0])
            result["last_host"] = str(hosts[-1])
        else:
            result["note"] = "No usable hosts (point-to-point or host route)"

        # Add helpful lab notes
        if net.prefixlen == 30:
            result["tip"] = "💡 /30 subnet — perfect for point-to-point serial links (2 usable IPs)"
        elif net.prefixlen == 24:
            result["tip"] = "💡 /24 subnet — common for LAN segments (254 usable IPs)"
        elif net.prefixlen == 32:
            result["tip"] = "💡 /32 — host route (single device)"

        return result

    except ValueError as e:
        return {"valid": False, "error": str(e)}


# ─────────────────────────────────────────────
#  CISCO CONFIG VALIDATION
# ─────────────────────────────────────────────

def validate_cisco_config(config_text):
    """
    Parse and validate a Cisco IOS configuration.
    Checks for common mistakes students make.
    """
    issues = []
    warnings = []
    good = []

    lines = config_text.strip().split('\n')
    lines = [l.rstrip() for l in lines if l.strip()]

    # Track current interface context
    current_interface = None
    interface_has_ip = False
    interface_has_no_shutdown = False
    interfaces_found = []

    # Check hostname
    hostname_lines = [l for l in lines if l.strip().lower().startswith('hostname')]
    if hostname_lines:
        good.append(f"✅ Hostname configured: {hostname_lines[0].strip()}")
    else:
        warnings.append("⚠️ No hostname configured — add: hostname [NAME]")

    for i, line in enumerate(lines):
        stripped = line.strip().lower()

        # Detect interface block start
        if stripped.startswith('interface '):
            # Save previous interface result
            if current_interface:
                if not interface_has_ip and 'loopback' not in current_interface.lower():
                    issues.append(f"❌ {current_interface} — missing 'ip address' command")
                if not interface_has_no_shutdown:
                    issues.append(f"❌ {current_interface} — missing 'no shutdown' (interface will stay DOWN)")
                else:
                    good.append(f"✅ {current_interface} — has IP and no shutdown")

            # Start new interface
            current_interface = line.strip()
            interface_has_ip = False
            interface_has_no_shutdown = False
            interfaces_found.append(current_interface)

        elif current_interface:
            if 'ip address' in stripped:
                interface_has_ip = True
                # Validate the IP in the command
                ip_match = re.search(r'ip address\s+(\S+)\s+(\S+)', stripped)
                if ip_match:
                    ip_result = validate_ip(ip_match.group(1))
                    mask_result = validate_subnet(f"{ip_match.group(1)}/{ip_match.group(2)}")
                    if not ip_result['valid']:
                        issues.append(f"❌ {current_interface} — invalid IP: {ip_match.group(1)}")
                    if not mask_result['valid']:
                        issues.append(f"❌ {current_interface} — invalid subnet mask: {ip_match.group(2)}")

            elif 'no shutdown' in stripped:
                interface_has_no_shutdown = True

            # Detect end of interface block
            elif not line.startswith(' ') and not line.startswith('\t') and stripped and not stripped.startswith('!'):
                if current_interface:
                    if not interface_has_ip and 'loopback' not in current_interface.lower() and 'vlan' not in current_interface.lower():
                        issues.append(f"❌ {current_interface} — missing 'ip address'")
                    if not interface_has_no_shutdown:
                        issues.append(f"❌ {current_interface} — missing 'no shutdown'")
                    else:
                        if interface_has_ip:
                            good.append(f"✅ {current_interface} — configured correctly")
                    current_interface = None

    # Check last interface
    if current_interface:
        if not interface_has_ip and 'loopback' not in current_interface.lower():
            issues.append(f"❌ {current_interface} — missing 'ip address'")
        if not interface_has_no_shutdown:
            issues.append(f"❌ {current_interface} — missing 'no shutdown'")
        elif interface_has_ip:
            good.append(f"✅ {current_interface} — configured correctly")

    # Check for routing
    has_rip = any('router rip' in l.lower() for l in lines)
    has_static = any('ip route' in l.lower() for l in lines)
    has_ospf = any('router ospf' in l.lower() for l in lines)

    if has_rip:
        good.append("✅ RIP routing configured")
        # Check RIP version
        has_version2 = any('version 2' in l.lower() for l in lines)
        if not has_version2:
            warnings.append("⚠️ RIP detected but no 'version 2' — add: version 2")
        has_no_auto = any('no auto-summary' in l.lower() for l in lines)
        if not has_no_auto:
            warnings.append("⚠️ RIP: add 'no auto-summary' to prevent routing issues")

    if has_static:
        good.append("✅ Static route(s) configured")

    if has_ospf:
        good.append("✅ OSPF routing configured")

    if not has_rip and not has_static and not has_ospf and len(interfaces_found) > 1:
        warnings.append("⚠️ No routing configured — devices may not reach each other")

    # Check for passwords (security)
    has_enable_secret = any('enable secret' in l.lower() for l in lines)
    has_enable_password = any('enable password' in l.lower() for l in lines)

    if has_enable_secret:
        good.append("✅ Enable secret configured (encrypted)")
    elif has_enable_password:
        warnings.append("⚠️ Using 'enable password' — prefer 'enable secret' (encrypted)")
    else:
        warnings.append("⚠️ No enable password set — device is unsecured")

    return {
        "valid": len(issues) == 0,
        "interfaces_found": len(interfaces_found),
        "issues": issues,
        "warnings": warnings,
        "good": good,
        "summary": f"Found {len(interfaces_found)} interface(s). {len(issues)} error(s), {len(warnings)} warning(s), {len(good)} check(s) passed."
    }


# ─────────────────────────────────────────────
#  EXTRACT IPs FROM ANY TEXT
# ─────────────────────────────────────────────

def extract_and_validate_ips(text):
    """
    Find all IP addresses in a text and validate them.
    Useful for validating config files automatically.
    """
    ip_pattern = r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'
    found_ips = re.findall(ip_pattern, text)

    results = []
    seen = set()

    for ip in found_ips:
        if ip not in seen:
            seen.add(ip)
            result = validate_ip(ip)
            results.append({"ip": ip, "result": result})

    return results


# ─────────────────────────────────────────────
#  FORMAT VALIDATION RESULTS AS TEXT
# ─────────────────────────────────────────────

def format_config_validation(validation_result):
    """Format config validation result as readable text for display"""
    lines = []
    lines.append(f"📋 **Config Validation Report**")
    lines.append(f"📊 {validation_result['summary']}\n")

    if validation_result['good']:
        lines.append("**✅ Passed Checks:**")
        for item in validation_result['good']:
            lines.append(f"  {item}")
        lines.append("")

    if validation_result['issues']:
        lines.append("**❌ Errors (must fix):**")
        for item in validation_result['issues']:
            lines.append(f"  {item}")
        lines.append("")

    if validation_result['warnings']:
        lines.append("**⚠️ Warnings (recommended to fix):**")
        for item in validation_result['warnings']:
            lines.append(f"  {item}")

    if validation_result['valid']:
        lines.append("\n🎉 **Config looks good! No critical errors found.**")
    else:
        lines.append(f"\n🔧 **Please fix the {len(validation_result['issues'])} error(s) above.**")

    return "\n".join(lines)

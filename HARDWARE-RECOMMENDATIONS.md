# Hardware Recommendations - MCP Infrastructure

## Current Deployment Specs (Container 200)

**Deployed on:** Proxmox VE LXC Container
**OS:** Debian-based (Ubuntu 22.04)
**Container Resources:**
- **CPU:** 6 cores
- **RAM:** 8GB
- **Storage:** 25GB
- **Network:** Bridge mode (vmbr0) with DHCP

**Services Running:**
- 5x Cloudflare Tunnel containers (existing)
- 6x MCP service containers (new)
  - Google (Gmail/Drive/Calendar)
  - iCloud (Mail/Calendar/Contacts)
  - Outlook (Email/Calendar)
  - Todoist (Task Management)
  - Integrator (Cross-service orchestration)
  - Hydraulic (AI schematic analysis)

## Recommended Home Server Build (10-Year Future-Proof)

### CPU
- **Minimum:** 8-core (16 threads) modern CPU
- **Recommended:** 12-16 core (24-32 threads)
- **Ideal:** AMD Ryzen 9 7900X / Intel i9-13900K or newer
- **Why:** AI workloads, multiple VMs/containers, transcoding

### RAM
- **Minimum:** 64GB DDR4/DDR5
- **Recommended:** 128GB DDR5
- **Configuration:** ECC RAM preferred for 24/7 operation
- **Why:** Memory-intensive AI models, multiple VMs, ZFS cache

### Storage

**Boot/System:**
- 2x 500GB NVMe SSD (RAID 1/mirror)
- PCIe 4.0 or 5.0

**VM/Container Storage:**
- 2TB+ NVMe SSD
- PCIe 4.0 minimum

**Data Storage:**
- 4-8x HDD (4TB-18TB each) in RAID-Z2 or RAID 10
- OR: Large capacity SSDs if budget allows

**Cache (Optional but recommended):**
- 256GB-1TB NVMe for ZFS L2ARC/SLOG

### Network
- **Minimum:** Dual 1GbE NICs
- **Recommended:** Dual 2.5GbE or 10GbE
- **Network Switch:** Managed switch with VLAN support

### Other Components

**Motherboard:**
- Multiple M.2 slots (3-4 minimum)
- ECC RAM support
- IPMI/BMC for remote management
- Adequate PCIe lanes (24+ recommended)

**Power Supply:**
- 750W-1000W 80+ Platinum/Titanium
- Modular preferred

**Case:**
- Rack-mount (4U) or tower with good airflow
- Hot-swap drive bays (8-12 bays)

**UPS:**
- 1500VA+ for runtime during power events
- Network-manageable preferred

**GPU (Optional):**
- For AI/ML workloads: NVIDIA RTX 4070+ or A4000+
- For transcoding: Intel QuickSync or NVIDIA P2000+

## Resource Allocation Strategy

### Proxmox Host Recommendations
- **Host OS:** Reserve 8-16GB RAM
- **ZFS ARC:** 25-50% of total RAM
- **VM/Container Pool:** Remaining RAM

### Example 128GB System Allocation
- Proxmox Host: 8GB
- ZFS ARC: 32-48GB
- VMs/Containers: 72-88GB

## Networking Architecture

**VLAN Segmentation:**
- VLAN 1: Management (Proxmox, IPMI)
- VLAN 10: LAN (trusted devices)
- VLAN 15: IoT/Home Automation (isolated)
- VLAN 20: DMZ (public-facing services via tunnel)

**Firewall:**
- OPNsense or pfSense VM with dedicated NICs
- 4GB RAM, 2 cores minimum

## Sample Budget Build (Mid-2025 Pricing)

**Option A: High-End ($3500-4500)**
- AMD Ryzen 9 9950X / Intel i9-14900K
- 128GB DDR5 ECC RAM
- 2x 1TB NVMe (boot)
- 2TB NVMe (VMs)
- 6x 8TB HDD (RAID-Z2 = 32TB usable)
- Dual 10GbE NIC
- 1000W PSU
- Rack case with hot-swap bays

**Option B: Mid-Range ($2000-2500)**
- AMD Ryzen 7 7900 / Intel i7-13700
- 64GB DDR4 ECC RAM
- 2x 500GB NVMe (boot)
- 1TB NVMe (VMs)
- 4x 4TB HDD (RAID 10 = 8TB usable)
- Dual 2.5GbE NIC
- 750W PSU
- Tower case

**Option C: Budget ($1200-1500)**
- AMD Ryzen 5 7600 / Intel i5-13400
- 32GB DDR4 RAM
- 2x 256GB NVMe (boot)
- 500GB NVMe (VMs)
- 2x 4TB HDD (mirror = 4TB usable)
- Single 2.5GbE NIC
- 650W PSU
- Tower case

## Current MCP Infrastructure Needs

**Per Container:**
- CPU: 0.5-1 core per MCP service
- RAM: 512MB-1GB per MCP service
- Storage: 100-500MB per service (Docker images)

**For 6 MCP Services:**
- CPU: 3-6 cores
- RAM: 3-6GB
- Storage: 5-10GB

**Cloudflare Tunnel:**
- CPU: Minimal (0.25 core)
- RAM: 128-256MB per tunnel
- Storage: <100MB

## Scaling Considerations

**For 10+ MCP Services:**
- CPU: 8-12 cores
- RAM: 12-16GB
- Storage: 30-50GB

**For AI-Heavy Workloads (like Hydraulic Analysis):**
- GPU highly recommended
- Additional 4-8GB RAM per AI service
- Fast NVMe for model caching

## Future-Proofing Strategies

1. **CPU:** Stick to AM5 (AMD) or LGA1700/1851 (Intel) platforms for upgrade path
2. **RAM:** Get motherboard with 4x DIMM slots, fill 2x now, expand later
3. **Storage:** Use ZFS or similar for flexible expansion
4. **Network:** Install 10GbE now even if switch comes later
5. **PCIe:** Ensure motherboard has slots for GPU, NVMe, NICs, HBAs
6. **Power:** Overspec PSU by 20-30% for future additions

## Backup Strategy

**3-2-1 Rule:**
- 3 copies of data
- 2 different media types
- 1 offsite backup

**For MCP Infrastructure:**
- Daily: Automated container snapshots (Proxmox)
- Weekly: Full backup to external drive
- Monthly: Offsite backup (cloud or physical location)
- **Critical:** Backup credentials separately (encrypted)

## Power Consumption Estimates

**Idle:**
- Mid-range build: 80-120W
- High-end build: 120-180W

**Under Load:**
- Mid-range build: 200-350W
- High-end build: 350-500W

**Annual Cost (@ $0.12/kWh, 80% idle time):**
- Mid-range: ~$120-150/year
- High-end: ~$180-220/year

## Maintenance Schedule

**Monthly:**
- Check disk health (SMART data)
- Review logs for errors
- Update containers/VMs

**Quarterly:**
- Clean dust filters
- Check UPS battery
- Verify backups restore successfully

**Annually:**
- Replace UPS batteries (if needed)
- Major Proxmox/OS updates
- Hardware inspection

---

**This configuration supports:**
- 20-30 LXC containers
- 10-15 VMs
- Multiple Docker stacks
- AI/ML workloads
- Media server (Plex/Jellyfin)
- Home automation (Home Assistant)
- Network services (Pi-hole, VPN, etc.)

**Tested with current deployment:** ✅ Successfully running 11 containers (5 tunnel + 6 MCP) on 8GB RAM, 6 cores

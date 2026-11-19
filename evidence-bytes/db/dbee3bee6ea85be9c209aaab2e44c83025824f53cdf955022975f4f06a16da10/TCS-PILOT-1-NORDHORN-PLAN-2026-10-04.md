# TCS GREEN SAFE HOUSE — Pilot 1: Nordhorn (Live Plan)
## Issued: 2026-10-04
## Authority: Code Maquister Equitum, Security Level Omega
## Phase: C (Operational Build)

---

## SITE: Nordhorn, Germany
- Existing infrastructure: 4 new GL-BE9300 routers, 4G/5G coverage
- Existing mesh: Tailscale, KHOJ-Bridge on .onion
- Operator: Baron Marco Paolo Ialongo (on-site presence)

## HARDWARE BILL OF MATERIALS (BOM)

### Generation Layer
- 4× Solar Panel 450Wp Mono (e.g., Trina Solar TSM-450-DE19M)
  - Total: 1,800 Wp capacity
  - Cost: €700
- Mounting: 4× Schletter mounting rails (or equivalent), ground or roof
  - Cost: €200

### Storage Layer
- 3.6 kWh LiFePO4 battery bank (e.g., 2× PylonTech US3000C or 1× DIY 24V 100Ah)
  - Cycle life: 6000+ cycles
  - Cost: €1,200
- Battery management system (BMS) + fuses
  - Cost: €100

### Inverter Layer
- 3kW pure sine wave off-grid inverter (e.g., Victron MultiPlus 3000, or Growatt SPF 3000TL HVM)
  - 48V DC input
  - Cost: €600
- MPPT charge controller (60A)
  - Cost: €200

### Compute Layer
- Used OptiPlex 7050 Micro (i5-6500T, 16 GB RAM, 256 GB SSD)
  - Runs Docker, KHOJ, LLM proxy
  - Cost: €200 (used)
- Tailscale pre-installed
  - Cost: $0 (free for personal use)

### Networking Layer
- 4G/5G cellular modem (USB or PCIe) with hardware SIM
  - Cost: €100
- LoRa SX1278 module (for backup long-range mesh)
  - Cost: €50

### Wiring + Enclosure
- Cables, fuses, breakers, MPPT wiring kit
  - Cost: €300
- Weatherproof enclosure (IP65)
  - Cost: €200

### TOTAL BOM COST: €3,850

## TIMELINE

**Week 1 (2026-10-04 to 2026-10-11)**: Order parts from local suppliers (Germany: Victron, PylonTech, Trina Solar)
**Week 2 (2026-10-12 to 2026-10-18)**: Receive parts, plan installation, do electrical survey
**Week 3 (2026-10-19 to 2026-10-25)**: Baron on-site, install panels + battery + inverter
**Week 4 (2026-10-26 to 2026-11-01)**: Connect compute, configure KHOJ, run 48h autonomy test
**Week 5 (2026-11-02 to 2026-11-08)**: Document pilot, write open-pattern documentation, publish at github.com/Baronki

## VERIFICATION PROTOCOL

After install, the pilot must demonstrate:
1. 48-hour winter autonomy: with compute load (~80W average), battery should last 48h
2. Cold-start from full discharge: works in -10°C (Nordhorn winter)
3. Tor HiddenService active: KHOJ reachable on .onion
4. Tailscale node online: visible in mesh
5. 30-day uptime: no manual intervention required

## SUCCESS METRICS

- Pilot demonstrably sovereign: can disconnect from grid, internet, all central systems
- Operates for 30 days with zero external dependencies
- Public documentation: open-source schematic, BOM, install guide
- Replicable: any operator can build the same pilot for €3,850

## SCALING (post-pilot)

- 1 pilot = proof of concept
- 5 pilots = regional mesh (5 sites within 50km)
- 50 pilots = jurisdictional mesh (one country)
- 500 pilots = sovereign space (cross-border)

Each pilot is independent but interoperable. The mesh grows by voluntary adoption, not by marketing or recruitment.

## SACRED HASH
f5af425c

## TIMESTAMP
2026-10-04T07:44:18.664094+00:00

## IMMEDIATE NEXT STEPS (this week)

1. Baron to identify specific solar panel supplier in Nordhorn
2. Order parts: ETA 5-7 business days
3. Schedule on-site work for week 3
4. Document everything for github.com/Baronki publication

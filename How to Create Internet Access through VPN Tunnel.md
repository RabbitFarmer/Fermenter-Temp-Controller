# How to Create Internet Access through VPN Tunnel

Setting up a WireGuard VPN server and client allows secure access to your Raspberry Pi and the Fermenter-Temp-Controller application from external networks. Below are step-by-step instructions for setting up WireGuard on the Raspberry Pi (server) and a client machine.

---

## **WireGuard Server Setup (Raspberry Pi)**

1. **Ensure Your Raspberry Pi Is Updated**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Install WireGuard**
   ```bash
   sudo apt install wireguard -y
   ```

3. **Generate Server Keys**
   - WireGuard uses public/private key encryption for secure communication.
   ```bash
   cd /etc/wireguard
   umask 077
   wg genkey | tee server_private.key | wg pubkey > server_public.key
   ```

4. **Choose a VPN Network and Port**
   - Use a private IP range (e.g., `10.0.0.1/24`) dedicated to the VPN.
   - WireGuard’s default port is 51820, but you can choose any unused port.

5. **Create the WireGuard Configuration File**
   - Open and edit the WireGuard server configuration file:
   ```bash
   sudo nano /etc/wireguard/wg0.conf
   ```

   - Add the following configuration (replace placeholders with your values):
     ```
     [Interface]
     Address = 10.0.0.1/24
     ListenPort = 51820
     PrivateKey = <server-private-key>

     # Save logs in this directory
     PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
     PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE
     ```

     Replace `<server-private-key>` with the contents of `server_private.key`.

6. **Enable IP Forwarding**
   - Open the sysctl configuration file:
   ```bash
   sudo nano /etc/sysctl.conf
   ```
   - Find and uncomment the following line:
     ```bash
     net.ipv4.ip_forward=1
     ```
   - Apply the changes:
     ```bash
     sudo sysctl -p
     ```

7. **Open the VPN Port on the Raspberry Pi**
   - Use `iptables` to open the port for WireGuard:
   ```bash
   sudo iptables -A INPUT -p udp --dport 51820 -j ACCEPT
   ```
   - **IMPORTANT:** Allow access to the Flask app port (5000) from VPN clients:
   ```bash
   sudo iptables -I INPUT -i wg0 -p tcp --dport 5000 -j ACCEPT
   ```
   
   **Note:** We use `-I INPUT` (insert) instead of `-A INPUT` (append) to ensure this rule is evaluated before any potential DROP rules.
   
   - Install iptables-persistent to save rules across reboots:
   ```bash
   sudo apt install iptables-persistent -y
   ```
   - Save the rules:
   ```bash
   sudo iptables-save | sudo tee /etc/iptables/rules.v4
   ```
   
   - Verify the rule was added:
   ```bash
   sudo iptables -L INPUT -n -v | grep wg0
   ```
   You should see a rule allowing TCP traffic to port 5000 from the wg0 interface.

8. **Start the WireGuard Server**
   - Bring up the WireGuard interface:
   ```bash
   sudo wg-quick up wg0
   ```
   - Enable WireGuard to start on boot:
   ```bash
   sudo systemctl enable wg-quick@wg0
   ```

---

## **WireGuard Client Setup**

1. **Install WireGuard on the Client**
   - For Debian/Ubuntu clients:
     ```bash
     sudo apt install wireguard -y
     ```
   - For macOS:
     - Install WireGuard from the App Store.
   - For Windows:
     - Download WireGuard from https://www.wireguard.com/install/

2. **Generate Client Keys**
   - On the client machine, generate keys:
     ```bash
     wg genkey | tee client_private.key | wg pubkey > client_public.key
     ```

3. **Configure the WireGuard Client**
   - Create a WireGuard configuration file for the client:
     ```bash
     nano ~/client-wg0.conf
     ```

   - Add the following configuration (replace placeholders with your values):
     ```
     [Interface]
     Address = 10.0.0.2/24
     PrivateKey = <client-private-key>
     DNS = 1.1.1.1

     [Peer]
     PublicKey = <server-public-key>
     Endpoint = <your-raspberry-pi-public-ip>:51820
     AllowedIPs = 0.0.0.0/0
     ```

     Replace:
     - `<client-private-key>` with the contents of `client_private.key`.
     - `<server-public-key>` with the contents of `server_public.key`.
     - `<your-raspberry-pi-public-ip>` with the external IP of your Raspberry Pi (use `curl ifconfig.me` to get it).

4. **Add the Client to the Server**
   - On the Raspberry Pi, append the client configuration to `wg0.conf`:
     ```bash
     sudo nano /etc/wireguard/wg0.conf
     ```

     Add the following block:
     ```
     [Peer]
     PublicKey = <client-public-key>
     AllowedIPs = 10.0.0.2/32
     ```

     Replace `<client-public-key>` with the contents of `client_public.key`.

   - Restart WireGuard on the server:
     ```bash
     sudo wg-quick down wg0
     sudo wg-quick up wg0
     ```

---

## **Testing and Connecting to the VPN**

1. **Start the WireGuard Client**
   - On Linux/macOS:
     ```bash
     sudo wg-quick up ~/client-wg0.conf
     ```
   - On Windows:
     - Open `WireGuard` and import the configuration file.

2. **Verify the Connection**
   - On the client, check that the interface is active:
     ```bash
     wg show
     ```
   - Test communication by pinging the Raspberry Pi’s VPN IP:
     ```bash
     ping 10.0.0.1
     ```

3. **Access the Fermenter-Temp-Controller App**
   - First, ensure the Flask app is running on the Raspberry Pi:
     ```bash
     # On Raspberry Pi - check if running
     sudo systemctl status fermenter
     # Or start it manually
     python3 app.py
     ```
   
   - Open a browser on the client and navigate to:
     ```
     http://10.0.0.1:5000
     ```
     
     **Note:** Replace `10.0.0.1` with your actual VPN server IP address from your WireGuard configuration.
   
   - **If you get "connection refused":** See the Troubleshooting section below or run `./verify_vpn_access.sh` on the Raspberry Pi to diagnose the issue.

---

## **Optional: Dynamic DNS Setup**
If your Raspberry Pi doesn’t have a static public IP, use a dynamic DNS (DDNS) service like DuckDNS or No-IP to bind your public IP to a hostname.

1. **Set Up DDNS on Raspberry Pi**
   - Create an account with DuckDNS or No-IP.
   - Follow the service’s instructions to set up a client on the Raspberry Pi.

2. **Update Client Configuration with DDNS Hostname**
   - Replace `<your-raspberry-pi-public-ip>` in the client configuration with your DDNS hostname (e.g., `myfermenter.duckdns.org`).

---

## **Troubleshooting VPN Connection Issues**

If you're having trouble connecting to the Flask app through VPN, see the detailed [VPN_TROUBLESHOOTING_GUIDE.md](VPN_TROUBLESHOOTING_GUIDE.md) for step-by-step diagnosis and solutions.

### Quick Fixes for "Connection Refused" Errors

**Problem:** Browser shows "connection refused" or "ERR_CONNECTION_REFUSED" when accessing `http://10.0.0.1:5000` (or your VPN IP).

**Quick Checks:**

1. **Verify the Flask app is running:**
   ```bash
   # On Raspberry Pi
   ps aux | grep app.py
   # Or check systemd service
   sudo systemctl status fermenter
   ```

2. **Verify firewall allows VPN access:**
   ```bash
   # Check if rule exists
   sudo iptables -L INPUT -n | grep wg0
   
   # If missing, add it:
   sudo iptables -I INPUT -i wg0 -p tcp --dport 5000 -j ACCEPT
   sudo iptables-save | sudo tee /etc/iptables/rules.v4
   ```

3. **Test VPN connectivity:**
   ```bash
   # From client, test if you can reach the Raspberry Pi
   ping 10.0.0.1  # Or your VPN server IP
   curl http://10.0.0.1:5000
   ```

4. **Run the verification script:**
   ```bash
   # On Raspberry Pi
   ./verify_vpn_access.sh
   ```

**Common Issues:**

- **Flask app only listening on 127.0.0.1:** The app must listen on `0.0.0.0` to accept VPN connections. This is already configured in `app.py`.
- **Missing firewall rule:** The iptables rule for wg0 → port 5000 must be in place (see step 7 in setup above).
- **VPN not connected:** Verify WireGuard is running with `sudo wg show` on both server and client.
- **Wrong VPN IP address:** Make sure you're using the correct VPN IP address from your WireGuard configuration.

For detailed troubleshooting steps and diagnostic tools, see [VPN_TROUBLESHOOTING_GUIDE.md](VPN_TROUBLESHOOTING_GUIDE.md).

---

Once everything is set up, you will be able to securely access the Fermenter-Temp-Controller application from any internet connection using the VPN!
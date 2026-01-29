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
   - Also allow access to the Flask app port (5000) from VPN clients:
   ```bash
   sudo iptables -A INPUT -i wg0 -p tcp --dport 5000 -j ACCEPT
   ```
   - Save the rules:
   ```bash
   sudo iptables-save > /etc/iptables/rules.v4
   ```

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
   - Open a browser on the client and navigate to:
     ```bash
     http://10.0.0.1:5000
     ```

---

## **Optional: Dynamic DNS Setup**
If your Raspberry Pi doesn’t have a static public IP, use a dynamic DNS (DDNS) service like DuckDNS or No-IP to bind your public IP to a hostname.

1. **Set Up DDNS on Raspberry Pi**
   - Create an account with DuckDNS or No-IP.
   - Follow the service’s instructions to set up a client on the Raspberry Pi.

2. **Update Client Configuration with DDNS Hostname**
   - Replace `<your-raspberry-pi-public-ip>` in the client configuration with your DDNS hostname (e.g., `myfermenter.duckdns.org`).

---

Once everything is set up, you will be able to securely access the Fermenter-Temp-Controller application from any internet connection using the VPN!
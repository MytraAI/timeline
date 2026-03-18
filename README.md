# Cloudy

Provision Google Cloud VMs pre-configured for AI-assisted development. Each VM comes with Claude Code, Codex CLI, Tailscale, git repos, and your git identity — ready to SSH into and start coding.

## Install (macOS)

```bash
gh release download --repo MytraAI/cloudy-ai --pattern "cloudy_darwin_$(uname -m | sed 's/x86_64/amd64/')*" --clobber && tar xzf cloudy_darwin_*.tar.gz && sudo mv cloudy /usr/local/bin/ && rm cloudy_darwin_*.tar.gz
```

Requires the [GitHub CLI](https://cli.github.com/) (`gh`) authenticated with access to the MytraAI org. macOS binaries are signed and notarized.

The CLI auto-checks for updates once per 24 hours. Run `cloudy update` to upgrade manually.

## Prerequisites

- A GCP project with Compute Engine enabled

### First-time setup

```bash
cloudy auth login
```

This opens your browser to authenticate via Google OAuth. No additional tools required.

### Building from source

Requires Go 1.24+ and Node.js 22+.

```bash
git clone git@github.com:MytraAI/cloudy-ai.git
cd cloudy-ai
make build
```

Add to your PATH:

```bash
ln -sf "$(pwd)/bin/cloudy" ~/bin/cloudy
```

## Configure

```bash
# Optional — explicit git identity (auto-discovered from GitHub if not set)
cloudy config set git.name "Jane Doe"
cloudy config set git.email "jane@example.com"

# Optional — SSH access from other devices (phone, tablet, etc.)
cloudy config set ssh.user mike_brevoort
cloudy config set ssh.public_key "ssh-ed25519 AAAA..."
```

See all options:

```bash
cloudy config list
```

## Usage

### Create a VM

```bash
cloudy create
```

Interactive prompts walk you through VM name, size, OS, and repo selection. If GitHub is connected (via OAuth or PAT), your repos are shown as a filterable list sorted by how often you use them.

### Non-interactive

```bash
cloudy create --name my-vm --size medium --repos https://github.com/org/repo.git --yes

# Spot/preemptible — ~70% cheaper but may be preempted by GCP
cloudy create --name my-vm --size xlarge --spot --yes
```

### VM Lifecycle

```bash
cloudy list                        # List all managed VMs
cloudy ssh <name>                  # SSH into a VM
cloudy ssh <name> --session <s>    # SSH into a specific session (worktree)
cloudy ssh forward <name> <port>   # Forward local port to VM via SSH
cloudy stop <name>                 # Stop (preserves disk, stops billing)
cloudy start <name>                # Start a stopped VM
cloudy suspend <name>              # Suspend (snapshots memory to disk)
cloudy resume <name>               # Resume a suspended VM
cloudy destroy <name>              # Delete VM and disk
cloudy init-script                 # Print/set per-user init script
cloudy sessions list <name>        # List sessions (git worktrees) on a VM
cloudy sessions create <name>      # Create a new session
cloudy sessions delete <name> <s>  # Delete a session
```

### SSH from Other Devices

Configure an SSH public key to access VMs from any device (phone, tablet, other machines):

```bash
cloudy config set ssh.user mike_brevoort
cloudy config set ssh.public_key "ssh-ed25519 AAAA..."
```

New VMs will have the key automatically. For existing VMs:

```bash
cloudy ssh-bootstrap <name>
```

Then connect directly: `ssh mike_brevoort@<vm-ip>` or via Tailscale hostname.

### Browser Terminal

The web UI includes a built-in terminal panel for SSH access directly from the browser. Once a VM's setup is complete, click **Terminal** to open an SSH session. The server acts as a WebSocket-to-SSH relay using managed SSH keypairs. Sessions persist across page navigation and support multiple tabs.

**Drag-and-drop file upload:** Drag files from your desktop onto the terminal panel to upload them to the VM. Files land at `~/uploads/` and the absolute path is automatically typed into the active terminal session — just like dragging a file onto Terminal.app on macOS.

### Per-User Init Script

Store a custom shell script that runs at the end of every VM provisioning:

```bash
cloudy init-script                 # Print current init script
cloudy init-script --edit          # Open in $EDITOR
```

Use this for personal setup like dotfiles, editor config, or additional tools without modifying the shared provisioning template.

### Shared Filesystem

Claude Code settings (`~/.claude`) are automatically synced across all your VMs via a GCSFuse-backed shared filesystem. Changes made on one VM are visible on all others.

### Tailscale

Tailscale is configured automatically via server-side OAuth when provisioning VMs. If a VM was created without Tailscale, you can install it retroactively:

```bash
cloudy tailscale-bootstrap <name>
```

## VM Sizes

| Size | Machine Type | vCPUs | Memory | Disk |
|------|-------------|-------|--------|------|
| small | e2-standard-2 | 2 | 8 GB | 50 GB |
| medium | e2-standard-4 | 4 | 16 GB | 100 GB |
| large | e2-standard-8 | 8 | 32 GB | 200 GB |
| xlarge | c3-highcpu-22 | 22 | 22 GB | 400 GB |

Any size can be combined with `--spot` for spot/preemptible pricing (~70% cheaper). Set a default: `cloudy config set defaults.size large`

## What Gets Installed on the VM

The default **Cloudy** image pre-bakes most dev tools into a GCE image so VMs boot fast. Two image families exist: `cloudy-full` (prod) and `cloudy-full-dev` (dev) — the server selects the right one based on `CLOUDY_ENV`. The startup script skips anything already installed.

- System packages (git, curl, build-essential, cmake, socat, jq, python3)
- Node.js 24.x LTS, nvm, Go, Rust, Deno
- Docker (with Buildx, Compose, docker-compose), PostgreSQL (installed, not auto-started), NATS
- kubectl, helm, k9s, Devbox, Conan
- pnpm, GitHub CLI, neovim, ripgrep, fd, htop, tmux, tree
- [Claude Code](https://claude.ai) (native installer, settings synced via shared filesystem)
- [Codex CLI](https://github.com/openai/codex)
- Tailscale (if auth key configured)
- Git credentials and identity
- Your selected repositories cloned to `~/`
- Heartbeat service (reports disk usage, uptime, load to server every 60s)
- Preemption detection hook (spot VMs — notifies server on GCE preemption)

Use `--os ubuntu` for a vanilla Ubuntu 24.04 image (all tools installed at boot).

---

## Local Development

```bash
make init          # Check tools, install Go + npm dependencies
cp .env.sample .env  # Fill in values (see comments in file)
make dev           # Start Go server + Vite dev server
```

`make dev` runs the Go API on `:8085` and Vite on `:5173` (proxying `/api` and `/auth` to Go).

### HTTPS with Tailscale Certs

The Vite dev server serves HTTPS using Tailscale-issued certs. This avoids self-signed certificate warnings and is required for Tailscale WASM browser terminals.

1. Enable HTTPS certificates in [Tailscale Admin → DNS](https://login.tailscale.com/admin/dns)
2. Generate certs for your dev machine:
   ```bash
   sudo tailscale cert --cert-file .certs/dev.crt --key-file .certs/dev.key $(tailscale status --json | jq -r '.Self.DNSName | rtrimstr(".")')
   sudo chown $USER .certs/dev.crt .certs/dev.key
   ```
3. Set `BASE_URL` in `.env` to your Tailscale FQDN with port 5173:
   ```
   BASE_URL=https://<machine-name>.<tailnet>.ts.net:5173
   ```
4. `make dev` — Vite auto-detects `.certs/dev.crt` and serves trusted HTTPS

Certs expire after 90 days — re-run step 2 to renew.

---

## Production Deployment

Cloudy has three deployment pipelines:

- **Server deploy** — pushes to `main` auto-deploy the web UI + API to Cloud Run
- **VM image build** — pushes to `main` that change `vm_images/**` build the prod GCE image via Packer (`build-vm-image.yml`). Dev images are built manually with `cd vm_images && make build-dev-full`.
- **CLI release** — pushing a `v*` tag builds cross-platform binaries, signs macOS builds, and publishes a GitHub Release

### 1. GCP Infrastructure Setup

Run the idempotent setup script to provision all GCP resources:

```bash
./scripts/setup-production.sh
```

This creates: Firestore database, Artifact Registry, service accounts, Workload Identity Federation, and Secret Manager secrets (`prod-cloudy-google-client-id`, `prod-cloudy-google-client-secret`, `prod-cloudy-session-secret`).

After running the setup script, manually create these additional optional secrets for GitHub and Tailscale integration:

```bash
# GitHub OAuth App (enables "Connect GitHub" in web UI)
echo -n "YOUR_CLIENT_ID" | gcloud secrets create prod-cloudy-github-client-id --data-file=- --project=mytra-ai-dev
echo -n "YOUR_CLIENT_SECRET" | gcloud secrets create prod-cloudy-github-client-secret --data-file=- --project=mytra-ai-dev

# Tailscale OAuth (enables centralized per-VM auth key minting)
echo -n "YOUR_CLIENT_ID" | gcloud secrets create prod-cloudy-tailscale-client-id --data-file=- --project=mytra-ai-dev
echo -n "YOUR_CLIENT_SECRET" | gcloud secrets create prod-cloudy-tailscale-client-secret --data-file=- --project=mytra-ai-dev
```

All Secret Manager secret names are prefixed with the environment (e.g. `prod-cloudy-*` for production, `dev-cloudy-*` for development). The `CLOUDY_ENV` environment variable controls this prefix and defaults to `dev`.

### 2. DNS

The server runs on Cloud Run. To map a custom domain:

```bash
# Create domain mapping (one-time)
gcloud beta run domain-mappings create \
  --service=cloudy \
  --domain=cloudy.artym.net \
  --region=us-central1 \
  --project=mytra-ai-dev

# Add CNAME record in Cloud DNS (artym.net zone is in the telemetry-monitor project)
gcloud dns record-sets create cloudy.artym.net. \
  --zone=artym-net \
  --type=CNAME \
  --rrdatas="ghs.googlehosted.com." \
  --ttl=300 \
  --project=telemetry-monitor
```

Google auto-provisions the TLS certificate once the CNAME propagates.

### 3. GitHub OAuth App (Optional)

To enable "Connect GitHub" in the web UI, create a GitHub OAuth App:

1. Go to [GitHub Developer Settings](https://github.com/settings/developers) > OAuth Apps > New OAuth App
2. Set **Authorization callback URL** to `https://cloudy.artym.net/auth/github/callback`
3. After creating, note the **Client ID** and generate a **Client Secret**
4. Store both as GCP secrets (see step 1 above)

When configured, users can connect their GitHub account with one click instead of manually creating a PAT. PATs are still supported and take precedence over OAuth tokens when both exist.

**For local development**, create a separate OAuth App with callback URL `http://localhost:8085/auth/github/callback` and add the credentials to your `.env` file (see `.env.sample`).

### 4. GitHub Repo Secrets

The repo requires two sets of secrets:

#### Server deploy + VM image build secrets (`.github/workflows/deploy.yml`, `build-vm-image.yml`)

| Secret | Description |
|--------|-------------|
| `WIF_PROVIDER` | Workload Identity Federation provider (output by setup script) |
| `WIF_SERVICE_ACCOUNT` | Deploy service account email (output by setup script) |
| `CLOUD_RUN_SA` | Runtime service account email (output by setup script) |
| `INITIAL_ADMIN_EMAIL` | First admin user's email |

The deploy workflow also mounts these GCP secrets as env vars at runtime: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `SESSION_SECRET`, `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `TAILSCALE_CLIENT_ID`, `TAILSCALE_CLIENT_SECRET`.

#### CLI release secrets (`.github/workflows/release.yml`)

| Secret | Description |
|--------|-------------|
| `APPLE_CERTIFICATE_BASE64` | Base64-encoded `.p12` containing Developer ID Application cert + private key |
| `APPLE_CERTIFICATE_PASSWORD` | Password used when exporting the `.p12` |
| `APPLE_ID` | Apple ID email for notarization |
| `APPLE_ID_APP_PASSWORD` | App-specific password from [appleid.apple.com](https://appleid.apple.com) |
| `APPLE_TEAM_ID` | 10-character Apple Team ID (e.g. `Q5T8FJNX57`) |
| `APPLE_TEAM_NAME` | Certificate holder name (e.g. `Brevoort Studio LLC`) |

### 5. macOS Code Signing Certificate

The release workflow signs and notarizes macOS binaries. This requires a **Developer ID Application** certificate (not "Apple Development" or "Apple Distribution").

**Creating the certificate:**

1. Open **Keychain Access** > Certificate Assistant > **Request a Certificate From a Certificate Authority**
2. Enter your email, select "Saved to disk", save the CSR file
3. Go to [Apple Developer Certificates](https://developer.apple.com/account/resources/certificates/list)
4. Click **+**, select **Developer ID Application**, choose **G2 Sub-CA**
5. Upload the CSR from step 2, download the `.cer`
6. Double-click the `.cer` to install it in Keychain Access

**Important:** Steps 2 and 6 must happen on the **same Mac** so the private key is linked to the certificate.

**Exporting the `.p12`:**

The Keychain Access UI may not offer `.p12` export even when the key is present. Use the command line:

```bash
# Verify the identity exists (must show "Developer ID Application: ...")
security find-identity -v -p codesigning

# Export as .p12
security export -k login.keychain-db -t identities -f pkcs12 -o /tmp/devid.p12 -P "your-password"

# Base64-encode and copy to clipboard
base64 -i /tmp/devid.p12 | pbcopy

# Clean up
rm /tmp/devid.p12
```

Set `APPLE_CERTIFICATE_BASE64` to the clipboard contents and `APPLE_CERTIFICATE_PASSWORD` to the password you used.

**Generating an app-specific password:**

1. Go to [appleid.apple.com](https://appleid.apple.com) > Sign-In and Security > App-Specific Passwords
2. Generate a new password, use it for `APPLE_ID_APP_PASSWORD`

### 6. Releasing a New Version

```bash
git tag v0.2.0
git push origin v0.2.0
```

The release workflow (`.github/workflows/release.yml`) runs on `macos-latest` and:
1. Builds web assets (`npm ci && npm run build`)
2. Cross-compiles for 5 targets via GoReleaser (darwin/linux amd64/arm64, windows amd64)
3. Signs and notarizes macOS binaries with `scripts/sign-macos.sh`
4. Creates a GitHub Release with archives and checksums

Users running older versions will see an update notice and can run `cloudy update`.

curl -L https://github.com/crynux-network/crynux-node/releases/download/v3.0.0/crynux-node-lithium-v3.0.0-mac-apple-silicon.dmg --output Crynux.dmg

# Unsigned app need to be explicitly handled with.
sudo xattr -ds com.apple.quarantine Crynux.dmg
open Crynux.dmg

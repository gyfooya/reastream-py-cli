#!/bin/bash

echo "=== Available ALSA devices ==="
aplay -l
echo "==============================="

read -p "Enter card number to use (e.g. 0,1,2): " CARD

echo "Using card: $CARD"

CONTROLS=("PCM" "Master" "Speaker" "Headphone")

for ctl in "${CONTROLS[@]}"; do
    echo "Setting $ctl to 100% on card $CARD"
    amixer -c "$CARD" set "$ctl" 100% 2>/dev/null
    amixer -c "$CARD" set "$ctl" unmute 2>/dev/null
done

echo "Saving ALSA state..."
sudo alsactl store

echo "Done."
[alarm@alarm REASTREAM-RX]$ 

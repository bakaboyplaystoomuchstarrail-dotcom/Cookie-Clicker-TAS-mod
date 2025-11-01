# Count clicks up to 2040ms
clicks = []
for t in range(0, 2041):
    if t % 20 == 0:
        clicks.append(t)

print(f"Clicks from 0-2040ms: {len(clicks)} clicks")
print(f"Times: {clicks[:10]}...")
print(f"Last few: ...{clicks[-5:]}")
print(f"Total cookies from clicks: {len(clicks)}")

# Count production frames up to 2040ms
ms_per_frame = 100 / 3
frames = []
last_frame = -1
for t in range(0, 2041):
    current_frame = int(t // ms_per_frame)
    if current_frame > last_frame:
        frames.append((t, current_frame))
        last_frame = current_frame

print(f"\nFrame transitions:")
for t, f in frames[:10]:
    print(f"  Frame {f} at {t}ms")
print(f"  ...")
for t, f in frames[-5:]:
    print(f"  Frame {f} at {t}ms")
print(f"\nTotal frames with production: {len(frames)}")
print(f"Frame at 2040ms: {int(2040 // ms_per_frame)}")

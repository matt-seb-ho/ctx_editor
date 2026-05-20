# Post-NeurIPS Mega Table (R3 snapshot)

Model × benchmark × method matrix across LiC / CollabLLM / WildChat.
All numbers below are accuracy% (LiC, CollabLLM) or s15/s3/augment **wins vs AO** quality% (WildChat).
Cells without a value have not been run yet.


## LiC


### LiC / math

| Variant | DeepSeek | gpt-5.4 | Kimi-K2.6 |
|---|---|---|---|
| **Baseline** | 72.2% (n=144) | 78.3% (n=143) | 75.5% (n=143) |
| **AO** | 86.1% (n=144) | 91.6% (n=143) | 84.6% (n=143) |
| **Augment** | 84.0% (n=144) | 86.7% (n=143) | 85.8% (n=134) |
| **Reset** | 81.9% (n=144) | 87.4% (n=143) | 83.6% (n=134) |
| **Gated-Reset** | 82.6% (n=144) | — | — |
| **Rewrite** | 73.6% (n=144) | 80.9% (n=141) | 79.7% (n=143) |


### LiC / code

| Variant | DeepSeek | gpt-5.4 | Kimi-K2.6 |
|---|---|---|---|
| **Baseline** | 34.5% (n=113) | 57.1% (n=119) | 58.4% (n=125) |
| **AO** | 60.2% (n=113) | 85.7% (n=119) | 64.8% (n=125) |
| **Augment** | 58.4% (n=113) | 74.8% (n=119) | 65.6% (n=125) |
| **Reset** | 59.3% (n=113) | 73.1% (n=119) | 66.4% (n=125) |
| **Gated-Reset** | 55.8% (n=113) | — | — |
| **Rewrite** | 28.3% (n=113) | 57.1% (n=119) | 52.0% (n=125) |


### LiC / database

| Variant | DeepSeek | gpt-5.4 | Kimi-K2.6 |
|---|---|---|---|
| **Baseline** | 22.4% (n=147) | 19.0% (n=147) | 19.0% (n=147) |
| **AO** | 45.6% (n=147) | 27.9% (n=147) | 30.6% (n=147) |
| **Augment** | 41.5% (n=147) | 56.5% (n=147) | 51.0% (n=147) |
| **Reset** | 49.0% (n=147) | 56.2% (n=146) | 55.1% (n=147) |
| **Gated-Reset** | 49.7% (n=147) | — | — |
| **Rewrite** | 27.9% (n=147) | 34.7% (n=147) | 36.7% (n=147) |


### LiC / actions

| Variant | DeepSeek | gpt-5.4 | Kimi-K2.6 |
|---|---|---|---|
| **Baseline** | 76.0% (n=150) | 87.3% (n=150) | 88.7% (n=150) |
| **AO** | 86.0% (n=150) | 92.7% (n=150) | 92.7% (n=150) |
| **Augment** | 84.0% (n=150) | 90.0% (n=150) | 92.7% (n=150) |
| **Reset** | 83.3% (n=150) | 92.0% (n=150) | 92.0% (n=150) |
| **Gated-Reset** | 85.3% (n=150) | — | — |
| **Rewrite** | 74.0% (n=150) | 84.0% (n=150) | 88.6% (n=149) |


## CollabLLM


### CollabLLM / math-hard

| Variant | DeepSeek | gpt-5.4 | Kimi-K2.6 |
|---|---|---|---|
| **Baseline** | 95.0% (n=20) | 95.0% (n=20) | 100.0% (n=20) |
| **AO** | 90.0% (n=20) | 95.0% (n=20) | 100.0% (n=20) |
| **Augment** | 100.0% (n=20) | 95.0% (n=20) | 95.0% (n=20) |
| **Reset** | 85.0% (n=20) | 93.8% (n=16) | 93.8% (n=16) |
| **Gated-Reset** | — | — | — |
| **Rewrite** | 90.0% (n=20) | — | — |


### CollabLLM / bigcodebench

| Variant | DeepSeek | gpt-5.4 | Kimi-K2.6 |
|---|---|---|---|
| **Baseline** | 5.0% (n=20) | 15.0% (n=20) | 15.0% (n=20) |
| **AO** | 15.0% (n=20) | 20.0% (n=20) | 26.3% (n=19) |
| **Augment** | 15.0% (n=20) | 17.6% (n=17) | 15.8% (n=19) |
| **Reset** | 20.0% (n=20) | — | — |
| **Gated-Reset** | — | — | — |
| **Rewrite** | 10.0% (n=20) | — | — |


## WildChat (Huang) — wins vs AO on quality

| Variant | gpt-5-mini | DeepSeek | Kimi-K2.6 |
|---|---|---|---|
| **Reset** | 89.8% (n=225) | 75.0% (n=76) | 71.6% (n=74) |
| **Augment** | 92.1% (n=227) | 84.2% (n=76) | 85.7% (n=70) |
| **Rewrite** | 86.7% (n=75) | 83.6% (n=73) | 82.1% (n=67) |
| **Gated-Reset** | — | — | — |

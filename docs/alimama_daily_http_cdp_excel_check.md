# 阿里妈妈日报 HTTP/CDP/Excel 核对报告

- Excel: `2026年阿里妈妈投放每日数据-4月1日至5月5日.xlsx`
- 日期范围: `2026-04-01` 至 `2026-05-05`
- 检查字段数: `5320`
- 缺失项: `0`
- 不一致项: `1191`

## 口径说明

- HTTP 使用本机 Chrome 登录态 Cookie。
- 品销宝 CDP 页面实际请求包含 `rptCampaignList2.json`，当前代码仍会在报告中暴露与 Excel 的差异。
- 万相台2 小计按当天 4 条明细重新汇总，不读取 Excel 小计缓存值。
- 投放日报公式按基础字段同一行计算，CPM = Cost / IMP * 1000。

## 差异汇总

- 明星店铺: 234
- 万相台: 228
- 万相台2/小计: 175
- 引力魔方: 170
- 万相台2/超级短视频: 117
- 万相台2/全站推广: 93
- 万相台2/超级直播: 67
- 直通车: 61
- 万相台2/货品运营: 46

## 高频字段

- shopping_cart: 161
- collection_cart_cost: 145
- collection_cart_rate: 142
- collection_cart_count: 141
- bookmark_product: 88
- cpm: 61
- roi: 60
- sales: 51
- cvr: 50
- order_count: 49
- bookmark_store: 41
- cpshopping_cart: 40
- cart_rate: 29
- cost: 29
- imp: 26
- asp: 20
- cporder: 20
- ctr: 20
- click: 9
- cpc: 9

## 差异明细（前 200 条）

| 日期 | Sheet | 字段 | Excel | HTTP |
|---|---|---|---:|---:|
| 2026-04-01 | 明星店铺 | order_count | 1 | 0 |
| 2026-04-01 | 明星店铺 | sales | 7857.00 | 0.00 |
| 2026-04-01 | 明星店铺 | shopping_cart | 28 | 10 |
| 2026-04-01 | 明星店铺 | bookmark_product | 3 | 0 |
| 2026-04-01 | 明星店铺 | bookmark_store | 7 | 5 |
| 2026-04-01 | 明星店铺 | roi | 6.1773 | 0.0000 |
| 2026-04-01 | 明星店铺 | cvr | 0.007143 | 0.000000 |
| 2026-04-01 | 明星店铺 | asp | 7857.00 |  |
| 2026-04-01 | 明星店铺 | cporder | 1271.92 |  |
| 2026-04-01 | 明星店铺 | cpshopping_cart | 45.43 | 127.19 |
| 2026-04-01 | 明星店铺 | cart_rate | 0.200000 | 0.071429 |
| 2026-04-01 | 引力魔方 | shopping_cart | 32 | 34 |
| 2026-04-01 | 引力魔方 | collection_cart_cost | 18.97 | 18.42 |
| 2026-04-01 | 引力魔方 | collection_cart_count | 67 | 69 |
| 2026-04-01 | 引力魔方 | collection_cart_rate | 0.045516 | 0.046875 |
| 2026-04-01 | 万相台 | cost | 3539.00 | 3538.85 |
| 2026-04-01 | 万相台 | shopping_cart | 53 | 55 |
| 2026-04-01 | 万相台 | bookmark_product | 9 | 10 |
| 2026-04-01 | 万相台 | roi | 10.6318 | 10.6323 |
| 2026-04-01 | 万相台 | collection_cart_cost | 57.08 | 54.44 |
| 2026-04-01 | 万相台 | collection_cart_count | 62 | 65 |
| 2026-04-01 | 万相台 | collection_cart_rate | 0.034311 | 0.035971 |
| 2026-04-01 | 万相台2/超级短视频 | shopping_cart | 21 | 22 |
| 2026-04-01 | 万相台2/超级短视频 | bookmark_product | 5 | 6 |
| 2026-04-01 | 万相台2/超级短视频 | collection_cart_cost | 34.60 | 32.13 |
| 2026-04-01 | 万相台2/超级短视频 | collection_cart_count | 26 | 28 |
| 2026-04-01 | 万相台2/超级短视频 | collection_cart_rate | 0.046346 | 0.049911 |
| 2026-04-01 | 万相台2/全站推广 | shopping_cart | 20 | 21 |
| 2026-04-01 | 万相台2/全站推广 | collection_cart_cost | 56.97 | 54.25 |
| 2026-04-01 | 万相台2/全站推广 | collection_cart_count | 20 | 21 |
| 2026-04-01 | 万相台2/全站推广 | collection_cart_rate | 0.027435 | 0.028807 |
| 2026-04-01 | 万相台2/小计 | shopping_cart | 53 | 55 |
| 2026-04-01 | 万相台2/小计 | bookmark_product | 9 | 10 |
| 2026-04-01 | 万相台2/小计 | collection_cart_cost | 57.08 | 54.44 |
| 2026-04-01 | 万相台2/小计 | collection_cart_count | 62 | 65 |
| 2026-04-01 | 万相台2/小计 | collection_cart_rate | 0.034311 | 0.035971 |
| 2026-04-02 | 明星店铺 | shopping_cart | 40 | 9 |
| 2026-04-02 | 明星店铺 | cpshopping_cart | 31.48 | 139.93 |
| 2026-04-02 | 明星店铺 | cart_rate | 0.264901 | 0.059603 |
| 2026-04-02 | 引力魔方 | shopping_cart | 20 | 21 |
| 2026-04-02 | 引力魔方 | bookmark_product | 54 | 57 |
| 2026-04-02 | 引力魔方 | cpm | 27.11 | 28.76 |
| 2026-04-02 | 引力魔方 | collection_cart_cost | 16.76 | 15.90 |
| 2026-04-02 | 引力魔方 | collection_cart_count | 74 | 78 |
| 2026-04-02 | 引力魔方 | collection_cart_rate | 0.044232 | 0.046623 |
| 2026-04-02 | 万相台 | cost | 3705.00 | 3704.98 |
| 2026-04-02 | 万相台 | order_count | 9 | 3 |
| 2026-04-02 | 万相台 | sales | 107418.00 | 45836.02 |
| 2026-04-02 | 万相台 | shopping_cart | 75 | 79 |
| 2026-04-02 | 万相台 | bookmark_product | 6 | 8 |
| 2026-04-02 | 万相台 | roi | 28.9927 | 12.3715 |
| 2026-04-02 | 万相台 | cvr | 0.003628 | 0.001209 |
| 2026-04-02 | 万相台 | collection_cart_cost | 45.74 | 42.59 |
| 2026-04-02 | 万相台 | collection_cart_count | 81 | 87 |
| 2026-04-02 | 万相台 | collection_cart_rate | 0.032648 | 0.035067 |
| 2026-04-02 | 万相台2/超级短视频 | shopping_cart | 26 | 28 |
| 2026-04-02 | 万相台2/超级短视频 | bookmark_product | 3 | 5 |
| 2026-04-02 | 万相台2/超级短视频 | collection_cart_cost | 30.86 | 27.12 |
| 2026-04-02 | 万相台2/超级短视频 | collection_cart_count | 29 | 33 |
| 2026-04-02 | 万相台2/超级短视频 | collection_cart_rate | 0.060291 | 0.068607 |
| 2026-04-02 | 万相台2/超级直播 | shopping_cart | 17 | 18 |
| 2026-04-02 | 万相台2/超级直播 | collection_cart_cost | 78.95 | 75.00 |
| 2026-04-02 | 万相台2/超级直播 | collection_cart_count | 19 | 20 |
| 2026-04-02 | 万相台2/超级直播 | collection_cart_rate | 0.032258 | 0.033956 |
| 2026-04-02 | 万相台2/全站推广 | order_count | 7 | 1 |
| 2026-04-02 | 万相台2/全站推广 | sales | 85025.02 | 23443.02 |
| 2026-04-02 | 万相台2/全站推广 | shopping_cart | 32 | 33 |
| 2026-04-02 | 万相台2/全站推广 | roi | 64.9096 | 17.8968 |
| 2026-04-02 | 万相台2/全站推广 | cvr | 0.004961 | 0.000709 |
| 2026-04-02 | 万相台2/全站推广 | collection_cart_cost | 39.69 | 38.53 |
| 2026-04-02 | 万相台2/全站推广 | collection_cart_count | 33 | 34 |
| 2026-04-02 | 万相台2/全站推广 | collection_cart_rate | 0.023388 | 0.024096 |
| 2026-04-02 | 万相台2/小计 | order_count | 9 | 3 |
| 2026-04-02 | 万相台2/小计 | sales | 107418.02 | 45836.02 |
| 2026-04-02 | 万相台2/小计 | shopping_cart | 75 | 79 |
| 2026-04-02 | 万相台2/小计 | bookmark_product | 6 | 8 |
| 2026-04-02 | 万相台2/小计 | roi | 28.9929 | 12.3715 |
| 2026-04-02 | 万相台2/小计 | cvr | 0.003628 | 0.001209 |
| 2026-04-02 | 万相台2/小计 | collection_cart_cost | 45.74 | 42.59 |
| 2026-04-02 | 万相台2/小计 | collection_cart_count | 81 | 87 |
| 2026-04-02 | 万相台2/小计 | collection_cart_rate | 0.032648 | 0.035067 |
| 2026-04-03 | 明星店铺 | shopping_cart | 48 | 5 |
| 2026-04-03 | 明星店铺 | bookmark_product | 2 | 1 |
| 2026-04-03 | 明星店铺 | cpshopping_cart | 26.04 | 249.99 |
| 2026-04-03 | 明星店铺 | cart_rate | 0.421053 | 0.043860 |
| 2026-04-03 | 引力魔方 | cpm | 28.76 | 23.86 |
| 2026-04-03 | 万相台 | cost | 4027.00 | 4026.97 |
| 2026-04-04 | 明星店铺 | shopping_cart | 22 | 7 |
| 2026-04-04 | 明星店铺 | cpshopping_cart | 56.85 | 178.66 |
| 2026-04-04 | 明星店铺 | cart_rate | 0.207547 | 0.066038 |
| 2026-04-04 | 引力魔方 | shopping_cart | 21 | 22 |
| 2026-04-04 | 引力魔方 | cpm | 23.86 | 19.09 |
| 2026-04-04 | 引力魔方 | collection_cart_cost | 11.86 | 11.75 |
| 2026-04-04 | 引力魔方 | collection_cart_count | 108 | 109 |
| 2026-04-04 | 引力魔方 | collection_cart_rate | 0.046253 | 0.046681 |
| 2026-04-04 | 万相台 | cost | 3219.00 | 3218.68 |
| 2026-04-04 | 万相台 | shopping_cart | 55 | 57 |
| 2026-04-04 | 万相台 | bookmark_product | 12 | 15 |
| 2026-04-04 | 万相台 | cpm | 37.20 | 37.19 |
| 2026-04-04 | 万相台 | roi | 2.8785 | 2.8788 |
| 2026-04-04 | 万相台 | collection_cart_cost | 48.04 | 44.70 |
| 2026-04-04 | 万相台 | collection_cart_count | 67 | 72 |
| 2026-04-04 | 万相台 | collection_cart_rate | 0.024302 | 0.026115 |
| 2026-04-04 | 万相台2/超级短视频 | shopping_cart | 19 | 20 |
| 2026-04-04 | 万相台2/超级短视频 | bookmark_product | 7 | 10 |
| 2026-04-04 | 万相台2/超级短视频 | collection_cart_cost | 34.61 | 29.99 |
| 2026-04-04 | 万相台2/超级短视频 | collection_cart_count | 26 | 30 |
| 2026-04-04 | 万相台2/超级短视频 | collection_cart_rate | 0.069892 | 0.080645 |
| 2026-04-04 | 万相台2/全站推广 | shopping_cart | 22 | 23 |
| 2026-04-04 | 万相台2/全站推广 | collection_cart_cost | 31.14 | 30.03 |
| 2026-04-04 | 万相台2/全站推广 | collection_cart_count | 27 | 28 |
| 2026-04-04 | 万相台2/全站推广 | collection_cart_rate | 0.016393 | 0.017001 |
| 2026-04-04 | 万相台2/小计 | shopping_cart | 55 | 57 |
| 2026-04-04 | 万相台2/小计 | bookmark_product | 12 | 15 |
| 2026-04-04 | 万相台2/小计 | collection_cart_cost | 48.04 | 44.70 |
| 2026-04-04 | 万相台2/小计 | collection_cart_count | 67 | 72 |
| 2026-04-04 | 万相台2/小计 | collection_cart_rate | 0.024302 | 0.026115 |
| 2026-04-05 | 明星店铺 | order_count | 2 | 1 |
| 2026-04-05 | 明星店铺 | sales | 19202.00 | 6512.00 |
| 2026-04-05 | 明星店铺 | shopping_cart | 15 | 4 |
| 2026-04-05 | 明星店铺 | bookmark_product | 1 | 0 |
| 2026-04-05 | 明星店铺 | bookmark_store | 4 | 5 |
| 2026-04-05 | 明星店铺 | roi | 15.1209 | 5.1280 |
| 2026-04-05 | 明星店铺 | cvr | 0.018182 | 0.009091 |
| 2026-04-05 | 明星店铺 | asp | 9601.00 | 6512.00 |
| 2026-04-05 | 明星店铺 | cporder | 634.95 | 1269.90 |
| 2026-04-05 | 明星店铺 | cpshopping_cart | 84.66 | 317.48 |
| 2026-04-05 | 明星店铺 | cart_rate | 0.136364 | 0.036364 |
| 2026-04-05 | 引力魔方 | shopping_cart | 24 | 28 |
| 2026-04-05 | 引力魔方 | bookmark_product | 70 | 71 |
| 2026-04-05 | 引力魔方 | cpm | 19.09 | 18.23 |
| 2026-04-05 | 引力魔方 | collection_cart_cost | 13.72 | 13.03 |
| 2026-04-05 | 引力魔方 | collection_cart_count | 94 | 99 |
| 2026-04-05 | 引力魔方 | collection_cart_rate | 0.032684 | 0.034423 |
| 2026-04-05 | 万相台 | cost | 3286.00 | 3286.04 |
| 2026-04-05 | 万相台 | shopping_cart | 43 | 52 |
| 2026-04-05 | 万相台 | bookmark_product | 6 | 8 |
| 2026-04-05 | 万相台 | roi | 13.3119 | 13.3118 |
| 2026-04-05 | 万相台 | collection_cart_cost | 67.06 | 54.77 |
| 2026-04-05 | 万相台 | collection_cart_count | 49 | 60 |
| 2026-04-05 | 万相台 | collection_cart_rate | 0.017151 | 0.021001 |
| 2026-04-05 | 万相台2/超级短视频 | shopping_cart | 15 | 18 |
| 2026-04-05 | 万相台2/超级短视频 | bookmark_product | 3 | 5 |
| 2026-04-05 | 万相台2/超级短视频 | collection_cart_cost | 49.89 | 39.05 |
| 2026-04-05 | 万相台2/超级短视频 | collection_cart_count | 18 | 23 |
| 2026-04-05 | 万相台2/超级短视频 | collection_cart_rate | 0.045802 | 0.058524 |
| 2026-04-05 | 万相台2/超级直播 | shopping_cart | 10 | 12 |
| 2026-04-05 | 万相台2/超级直播 | collection_cart_cost | 122.76 | 105.22 |
| 2026-04-05 | 万相台2/超级直播 | collection_cart_count | 12 | 14 |
| 2026-04-05 | 万相台2/超级直播 | collection_cart_rate | 0.022556 | 0.026316 |
| 2026-04-05 | 万相台2/全站推广 | shopping_cart | 18 | 22 |
| 2026-04-05 | 万相台2/全站推广 | collection_cart_cost | 48.15 | 39.78 |
| 2026-04-05 | 万相台2/全站推广 | collection_cart_count | 19 | 23 |
| 2026-04-05 | 万相台2/全站推广 | collection_cart_rate | 0.009834 | 0.011905 |
| 2026-04-05 | 万相台2/小计 | shopping_cart | 43 | 52 |
| 2026-04-05 | 万相台2/小计 | bookmark_product | 6 | 8 |
| 2026-04-05 | 万相台2/小计 | collection_cart_cost | 67.06 | 54.77 |
| 2026-04-05 | 万相台2/小计 | collection_cart_count | 49 | 60 |
| 2026-04-05 | 万相台2/小计 | collection_cart_rate | 0.017151 | 0.021001 |
| 2026-04-06 | 明星店铺 | shopping_cart | 20 | 9 |
| 2026-04-06 | 明星店铺 | bookmark_product | 1 | 0 |
| 2026-04-06 | 明星店铺 | bookmark_store | 4 | 3 |
| 2026-04-06 | 明星店铺 | cpshopping_cart | 63.97 | 142.15 |
| 2026-04-06 | 明星店铺 | cart_rate | 0.151515 | 0.068182 |
| 2026-04-06 | 直通车 | bookmark_store | 2 | 3 |
| 2026-04-06 | 引力魔方 | shopping_cart | 19 | 20 |
| 2026-04-06 | 引力魔方 | cpm | 18.23 | 16.42 |
| 2026-04-06 | 引力魔方 | collection_cart_cost | 14.61 | 14.45 |
| 2026-04-06 | 引力魔方 | collection_cart_count | 87 | 88 |
| 2026-04-06 | 引力魔方 | collection_cart_rate | 0.029382 | 0.029720 |
| 2026-04-06 | 万相台 | cost | 6085.00 | 6085.07 |
| 2026-04-06 | 万相台 | shopping_cart | 79 | 85 |
| 2026-04-06 | 万相台 | bookmark_product | 10 | 12 |
| 2026-04-06 | 万相台 | bookmark_store | 6 | 7 |
| 2026-04-06 | 万相台 | roi | 6.4066 | 6.4065 |
| 2026-04-06 | 万相台 | collection_cart_cost | 68.37 | 62.73 |
| 2026-04-06 | 万相台 | collection_cart_count | 89 | 97 |
| 2026-04-06 | 万相台 | collection_cart_rate | 0.026153 | 0.028504 |
| 2026-04-06 | 万相台2/超级短视频 | shopping_cart | 28 | 33 |
| 2026-04-06 | 万相台2/超级短视频 | bookmark_product | 3 | 4 |
| 2026-04-06 | 万相台2/超级短视频 | collection_cart_cost | 29.03 | 24.32 |
| 2026-04-06 | 万相台2/超级短视频 | collection_cart_count | 31 | 37 |
| 2026-04-06 | 万相台2/超级短视频 | collection_cart_rate | 0.070615 | 0.084282 |
| 2026-04-06 | 万相台2/超级直播 | shopping_cart | 35 | 36 |
| 2026-04-06 | 万相台2/超级直播 | bookmark_product | 4 | 5 |
| 2026-04-06 | 万相台2/超级直播 | bookmark_store | 2 | 3 |
| 2026-04-06 | 万相台2/超级直播 | collection_cart_cost | 102.56 | 97.56 |
| 2026-04-06 | 万相台2/超级直播 | collection_cart_count | 39 | 41 |
| 2026-04-06 | 万相台2/超级直播 | collection_cart_rate | 0.024164 | 0.025403 |
| 2026-04-06 | 万相台2/小计 | shopping_cart | 79 | 85 |
| 2026-04-06 | 万相台2/小计 | bookmark_product | 10 | 12 |
| 2026-04-06 | 万相台2/小计 | bookmark_store | 6 | 7 |
| 2026-04-06 | 万相台2/小计 | collection_cart_cost | 68.37 | 62.73 |
| 2026-04-06 | 万相台2/小计 | collection_cart_count | 89 | 97 |
| 2026-04-06 | 万相台2/小计 | collection_cart_rate | 0.026153 | 0.028504 |
| 2026-04-07 | 明星店铺 | order_count | 3 | 2 |
| 2026-04-07 | 明星店铺 | sales | 31592.00 | 21594.00 |
| 2026-04-07 | 明星店铺 | shopping_cart | 14 | 7 |
| 2026-04-07 | 明星店铺 | bookmark_product | 1 | 0 |
| 2026-04-07 | 明星店铺 | roi | 53.2910 | 36.4259 |

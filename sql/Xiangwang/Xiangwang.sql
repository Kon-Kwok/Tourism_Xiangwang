-- =========================================
-- Xiangwang unified schema
-- Generated from current MySQL database: Xiangwang
-- =========================================
CREATE DATABASE IF NOT EXISTS `Xiangwang` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `Xiangwang`;

DROP TABLE IF EXISTS `collection_batches`;
CREATE TABLE `collection_batches` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '批次ID',
  `page_code` varchar(64) NOT NULL COMMENT '页面编码',
  `biz_date` date NOT NULL COMMENT '业务日期',
  `shop_name` varchar(255) NOT NULL COMMENT '店铺名称',
  `status` varchar(32) NOT NULL COMMENT '批次状态',
  `started_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
  `finished_at` timestamp NULL DEFAULT NULL COMMENT '结束时间',
  `error_message` text COMMENT '错误信息',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='生意参谋采集批次';

DROP TABLE IF EXISTS `customer_service_data_daily`;
CREATE TABLE `customer_service_data_daily` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `日期` date NOT NULL COMMENT '日期',
  `旺旺` varchar(100) DEFAULT NULL COMMENT '旺旺',
  `接待人数` int DEFAULT NULL COMMENT '接待人数',
  `平均响应秒` decimal(8,2) DEFAULT NULL COMMENT '平均响应(秒)',
  `回复率` decimal(4,3) DEFAULT NULL COMMENT '回复率',
  `询单最终付款成功率` decimal(6,4) DEFAULT NULL COMMENT '询单->最终付款成功率',
  `上班天数` decimal(4,1) DEFAULT NULL COMMENT '上班天数',
  `评价发送率` decimal(6,4) DEFAULT NULL COMMENT '评价发送率',
  `客户满意比` varchar(10) DEFAULT NULL COMMENT '客户满意比',
  `很满意` varchar(10) DEFAULT NULL COMMENT '很满意',
  `满意` varchar(10) DEFAULT NULL COMMENT '满意',
  `一般` varchar(10) DEFAULT NULL COMMENT '一般',
  `不满意` varchar(10) DEFAULT NULL COMMENT '不满意',
  `很不满意` varchar(10) DEFAULT NULL COMMENT '很不满意',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_日期` (`日期`),
  KEY `idx_旺旺` (`旺旺`)
) ENGINE=InnoDB AUTO_INCREMENT=781 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='飞猪客服数据汇总日数据';

DROP TABLE IF EXISTS `customer_service_data_weekly`;
CREATE TABLE `customer_service_data_weekly` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `日期` varchar(20) DEFAULT NULL COMMENT '日期(周范围)',
  `旺旺` varchar(100) DEFAULT NULL COMMENT '旺旺',
  `接待人数` int DEFAULT NULL COMMENT '接待人数',
  `平均响应秒` decimal(8,2) DEFAULT NULL COMMENT '平均响应(秒)',
  `回复率` tinyint DEFAULT NULL COMMENT '回复率',
  `询单最终付款成功率` tinyint DEFAULT NULL COMMENT '询单->最终付款成功率',
  `上班天数` decimal(4,1) DEFAULT NULL COMMENT '上班天数',
  `评价发送率` decimal(6,4) DEFAULT NULL COMMENT '评价发送率',
  `客户满意比` tinyint DEFAULT NULL COMMENT '客户满意比',
  `很满意` int DEFAULT NULL COMMENT '很满意',
  `满意` int DEFAULT NULL COMMENT '满意',
  `一般` int DEFAULT NULL COMMENT '一般',
  `不满意` int DEFAULT NULL COMMENT '不满意',
  `很不满意` int DEFAULT NULL COMMENT '很不满意',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_日期` (`日期`),
  KEY `idx_旺旺` (`旺旺`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='飞猪客服数据汇总周数据';

DROP TABLE IF EXISTS `customer_service_performance_summary`;
CREATE TABLE `customer_service_performance_summary` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `旺旺昵称` varchar(100) DEFAULT NULL COMMENT '旺旺昵称',
  `咨询人数` int DEFAULT NULL COMMENT '咨询人数',
  `接待人数` int DEFAULT NULL COMMENT '接待人数',
  `询单人数` varchar(20) DEFAULT NULL COMMENT '询单人数',
  `销售额` decimal(14,2) DEFAULT NULL COMMENT '销售额',
  `销售量` int DEFAULT NULL COMMENT '销售量',
  `销售人数` int DEFAULT NULL COMMENT '销售人数',
  `订单数` int DEFAULT NULL COMMENT '订单数',
  `date_time` date DEFAULT NULL COMMENT 'Date',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_旺旺昵称` (`旺旺昵称`),
  KEY `idx_date_time` (`date_time`)
) ENGINE=InnoDB AUTO_INCREMENT=769 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='飞猪客服绩效汇总';

DROP TABLE IF EXISTS `customer_service_performance_workload_analysis`;
CREATE TABLE `customer_service_performance_workload_analysis` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `旺旺昵称` varchar(100) DEFAULT NULL COMMENT '旺旺昵称',
  `咨询人数` int DEFAULT NULL COMMENT '咨询人数',
  `接待人数` int DEFAULT NULL COMMENT '接待人数',
  `直接接待人数` int DEFAULT NULL COMMENT '直接接待人数',
  `转入人数` int DEFAULT NULL COMMENT '转入人数',
  `转出人数` int DEFAULT NULL COMMENT '转出人数',
  `总消息` int DEFAULT NULL COMMENT '总消息',
  `买家消息` int DEFAULT NULL COMMENT '买家消息',
  `客服消息` int DEFAULT NULL COMMENT '客服消息',
  `答问比` decimal(6,4) DEFAULT NULL COMMENT '答问比',
  `客服字数` int DEFAULT NULL COMMENT '客服字数',
  `最大同时接待` decimal(6,1) DEFAULT NULL COMMENT '最大同时接待',
  `未回复人数` int DEFAULT NULL COMMENT '未回复人数',
  `旺旺回复率` decimal(4,3) DEFAULT NULL COMMENT '旺旺回复率',
  `慢响应人数` int DEFAULT NULL COMMENT '慢响应人数',
  `长接待人数` int DEFAULT NULL COMMENT '长接待人数',
  `首次响应秒` decimal(8,2) DEFAULT NULL COMMENT '首次响应(秒)',
  `平均响应秒` decimal(8,2) DEFAULT NULL COMMENT '平均响应(秒)',
  `平均接待秒` varchar(20) DEFAULT NULL COMMENT '平均接待(秒)',
  `平均接待时长秒` decimal(8,2) DEFAULT NULL COMMENT '平均接待时长(秒)',
  `date_time` date DEFAULT NULL COMMENT 'Date',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_旺旺昵称` (`旺旺昵称`),
  KEY `idx_date_time` (`date_time`)
) ENGINE=InnoDB AUTO_INCREMENT=769 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='飞猪客服绩效工作量分析';

DROP TABLE IF EXISTS `gravity_rubiks_cube`;
CREATE TABLE `gravity_rubiks_cube` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `date_time` date NOT NULL COMMENT 'Date 时间',
  `cost` varchar(32) DEFAULT NULL COMMENT 'Cost 花费',
  `imp` bigint DEFAULT NULL COMMENT 'IMP 展示',
  `click` bigint DEFAULT NULL COMMENT 'Click 点击',
  `order_count` bigint DEFAULT NULL COMMENT 'Order 订单',
  `sales` varchar(32) DEFAULT NULL COMMENT 'Sales 销量',
  `shopping_cart` bigint DEFAULT NULL COMMENT 'ShoppingCart 加入购物车',
  `bookmark_product` bigint DEFAULT NULL COMMENT 'Bookmark-Product 宝贝收藏',
  `bookmark_store` bigint DEFAULT NULL COMMENT 'Bookmark-Store 店铺收藏',
  `ctr` varchar(16) DEFAULT NULL COMMENT 'CTR 点击率',
  `cpc` varchar(32) DEFAULT NULL COMMENT 'CPC 点击成本',
  `cpm` varchar(32) DEFAULT NULL COMMENT 'CPM 拉新成本',
  `roi` decimal(10,4) DEFAULT NULL COMMENT 'ROI 投资回报率',
  `cvr` varchar(16) DEFAULT NULL COMMENT 'CVR 点击转化率',
  `collection_cart_cost` varchar(32) DEFAULT NULL COMMENT '收藏加购成本',
  `collection_cart_count` bigint DEFAULT NULL COMMENT '收藏加购量',
  `collection_cart_rate` varchar(16) DEFAULT NULL COMMENT '收藏加购率',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_date_time` (`date_time`)
) ENGINE=InnoDB AUTO_INCREMENT=36 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='飞猪引力魔方';

DROP TABLE IF EXISTS `homepage_metrics`;
CREATE TABLE `homepage_metrics` (
  `biz_date` date NOT NULL COMMENT '业务日期',
  `page_code` varchar(64) NOT NULL COMMENT '页面编码',
  `shop_name` varchar(255) NOT NULL COMMENT '店铺名称',
  `metric_code` varchar(128) NOT NULL COMMENT '指标编码',
  `metric_value` decimal(20,6) DEFAULT NULL COMMENT '指标值',
  `cycle_crc` decimal(20,10) DEFAULT NULL COMMENT '环比',
  `sync_crc` decimal(20,10) DEFAULT NULL COMMENT '同比/对比',
  `year_sync_crc` decimal(20,10) DEFAULT NULL COMMENT '去年同期',
  `collected_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '采集时间',
  `batch_id` bigint NOT NULL COMMENT '批次ID',
  PRIMARY KEY (`biz_date`,`page_code`,`metric_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='生意参谋首页核心指标';

DROP TABLE IF EXISTS `homepage_trends`;
CREATE TABLE `homepage_trends` (
  `biz_date` date NOT NULL COMMENT '业务日期',
  `stat_date` date NOT NULL COMMENT '统计日期',
  `page_code` varchar(64) NOT NULL COMMENT '页面编码',
  `shop_name` varchar(255) NOT NULL COMMENT '店铺名称',
  `metric_code` varchar(128) NOT NULL COMMENT '指标编码',
  `self_value` decimal(20,6) DEFAULT NULL COMMENT '本店值',
  `rival_avg_value` decimal(20,6) DEFAULT NULL COMMENT '同行同层均值',
  `rival_good_value` decimal(20,6) DEFAULT NULL COMMENT '同行优秀值',
  `collected_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '采集时间',
  `batch_id` bigint NOT NULL COMMENT '批次ID',
  PRIMARY KEY (`biz_date`,`stat_date`,`page_code`,`metric_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='生意参谋首页趋势序列';

DROP TABLE IF EXISTS `order_list`;
CREATE TABLE `order_list` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `order_id` varchar(50) NOT NULL,
  `item_title` varchar(300) DEFAULT NULL,
  `package_type` varchar(200) DEFAULT NULL,
  `buy_mount` int DEFAULT NULL,
  `actual_fee` decimal(10,2) DEFAULT NULL,
  `order_time` datetime DEFAULT NULL,
  `status_text` varchar(50) DEFAULT NULL,
  `order_date` date DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_order_date` (`order_date`),
  KEY `idx_order_id` (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP TABLE IF EXISTS `shop_daily_key_data`;
CREATE TABLE `shop_daily_key_data` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `日期` date NOT NULL COMMENT '日期',
  `total_pv` bigint DEFAULT NULL COMMENT 'Total PV (总浏览数)',
  `total_uv` bigint DEFAULT NULL COMMENT 'Total UV(总访客数)',
  `流量来源广告_uv` bigint DEFAULT NULL COMMENT '流量来源广告UV',
  `流量来源平台_uv` bigint DEFAULT NULL COMMENT '流量来源平台UV',
  `流量来源汇总` bigint DEFAULT NULL COMMENT '流量来源汇总',
  `直引万品点击量` bigint DEFAULT NULL COMMENT '直引万品点击量',
  `chat_volume` bigint DEFAULT NULL COMMENT 'Chat Volume(询单量)',
  `total_bookings` bigint DEFAULT NULL COMMENT 'Total Bookings(总售卖件数)',
  `total_pax` decimal(10,2) DEFAULT NULL COMMENT 'Total PAX(总售卖乘客数)',
  `gmv` decimal(14,2) DEFAULT NULL COMMENT 'GMV',
  `pingxiaobao_cost` decimal(14,2) DEFAULT NULL COMMENT '品销宝费用',
  `pingxiaobao_imp` bigint DEFAULT NULL COMMENT '品销宝展示',
  `pingxiaobao_click` bigint DEFAULT NULL COMMENT '品销宝点击',
  `tmall_express_cost` decimal(14,2) DEFAULT NULL COMMENT '直通车费用',
  `tmall_express_imp` bigint DEFAULT NULL COMMENT '直通车展示',
  `tmall_express_click` bigint DEFAULT NULL COMMENT '直通车点击',
  `gravity_rubiks_cube_cost` decimal(14,2) DEFAULT NULL COMMENT '引力魔方费用',
  `gravity_rubiks_cube_imp` bigint DEFAULT NULL COMMENT '引力魔方展示',
  `gravity_rubiks_cube_click` bigint DEFAULT NULL COMMENT '引力魔方点击',
  `mansa_dae_cost` decimal(14,2) DEFAULT NULL COMMENT '万相台费用',
  `mansa_dae_views` bigint DEFAULT NULL COMMENT '万相台观看量',
  `mansa_dae_click` bigint DEFAULT NULL COMMENT '万相台点击',
  `super_recommendation_cost` decimal(14,2) DEFAULT NULL COMMENT '超推Cost',
  `cost_total` decimal(14,2) DEFAULT NULL COMMENT 'Cost Total',
  `imp_total` bigint DEFAULT NULL COMMENT 'IMP Total',
  `click_total` bigint DEFAULT NULL COMMENT 'Click Total',
  `pingxiaobao_booked_cabin` decimal(10,2) DEFAULT NULL COMMENT '品销宝Booked Cabin',
  `tmall_express_booked_cabin` bigint DEFAULT NULL COMMENT '直通车Booked Cabin',
  `gravity_rubiks_cube_booked_cabin` decimal(10,2) DEFAULT NULL COMMENT '引力魔方Booked Cabin',
  `mansa_dae_booked_cabin` decimal(10,2) DEFAULT NULL COMMENT '万相台Booked Cabin',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_日期` (`日期`)
) ENGINE=InnoDB AUTO_INCREMENT=36 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='千牛飞猪店铺日度关键数据';

DROP TABLE IF EXISTS `shop_data_daily_registration`;
CREATE TABLE `shop_data_daily_registration` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `日期` date NOT NULL COMMENT '日期',
  `PV` bigint DEFAULT NULL COMMENT 'PV',
  `UV` bigint DEFAULT NULL COMMENT 'UV',
  `PaidUV` int DEFAULT NULL COMMENT 'PaidUV',
  `关注店铺人数` int DEFAULT NULL COMMENT '关注店铺人数',
  `GMV` decimal(14,2) DEFAULT NULL COMMENT 'GMV',
  `咨询人数` int DEFAULT NULL COMMENT '咨询人数',
  `咨询转化率` decimal(10,6) DEFAULT NULL COMMENT '咨询转化率',
  `下单买家数` int DEFAULT NULL COMMENT '下单买家数',
  `下单转化率` decimal(10,6) DEFAULT NULL COMMENT '下单转化率',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_日期` (`日期`)
) ENGINE=InnoDB AUTO_INCREMENT=53 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='千牛店铺数据每日登记';

DROP TABLE IF EXISTS `star_store`;
CREATE TABLE `star_store` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `date_time` date NOT NULL COMMENT 'Date 时间',
  `cost` varchar(32) DEFAULT NULL COMMENT 'Cost 花费',
  `imp` bigint DEFAULT NULL COMMENT 'IMP 展示',
  `click` bigint DEFAULT NULL COMMENT 'Click 点击',
  `order_count` bigint DEFAULT NULL COMMENT 'Order 订单',
  `sales` varchar(32) DEFAULT NULL COMMENT 'Sales 销量',
  `shopping_cart` bigint DEFAULT NULL COMMENT 'ShoppingCart 加入购物车',
  `bookmark_product` bigint DEFAULT NULL COMMENT 'Bookmark-Product 宝贝收藏',
  `bookmark_store` bigint DEFAULT NULL COMMENT 'Bookmark-Store 店铺收藏',
  `ctr` varchar(16) DEFAULT NULL COMMENT 'CTR 点击率',
  `cpc` varchar(32) DEFAULT NULL COMMENT 'CPC 点击成本',
  `cpm` varchar(32) DEFAULT NULL COMMENT 'CPM 千次展现成本',
  `roi` decimal(10,4) DEFAULT NULL COMMENT 'ROI 投资回报率',
  `cvr` varchar(16) DEFAULT NULL COMMENT 'CVR 点击转化率',
  `asp` varchar(32) DEFAULT NULL COMMENT 'ASP 订单均价',
  `cporder` varchar(32) DEFAULT NULL COMMENT 'Cporder 订单成本',
  `cpshopping_cart` varchar(32) DEFAULT NULL COMMENT 'CPshopping cart 加购成本',
  `cart_rate` varchar(16) DEFAULT NULL COMMENT '加购率',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_date_time` (`date_time`)
) ENGINE=InnoDB AUTO_INCREMENT=36 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='飞猪明星店铺';

DROP TABLE IF EXISTS `tmall_express`;
CREATE TABLE `tmall_express` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `date_time` date NOT NULL COMMENT 'Date 时间',
  `cost` varchar(32) DEFAULT NULL COMMENT 'Cost 花费',
  `imp` bigint DEFAULT NULL COMMENT 'IMP 展示',
  `click` bigint DEFAULT NULL COMMENT 'Click 点击',
  `order_count` bigint DEFAULT NULL COMMENT 'Order 订单',
  `sales` varchar(32) DEFAULT NULL COMMENT 'Sales 销量GMV',
  `shopping_cart` bigint DEFAULT NULL COMMENT 'ShoppingCart 加入购物车',
  `bookmark_product` bigint DEFAULT NULL COMMENT 'Bookmark-Product 宝贝收藏',
  `bookmark_store` bigint DEFAULT NULL COMMENT 'Bookmark-Store 店铺收藏',
  `ctr` varchar(16) DEFAULT NULL COMMENT 'CTR 点击率',
  `cpc` varchar(32) DEFAULT NULL COMMENT 'CPC 点击成本',
  `roi` decimal(10,4) DEFAULT NULL COMMENT 'ROI 投资回报率',
  `cvr` varchar(16) DEFAULT NULL COMMENT 'CVR 点击转化率',
  `asp` varchar(32) DEFAULT NULL COMMENT 'ASP 订单均价',
  `cporder` varchar(32) DEFAULT NULL COMMENT 'Cporder 订单成本',
  `cpshopping_cart` varchar(32) DEFAULT NULL COMMENT 'CPshopping cart 加购成本',
  `collection_cart_cost` varchar(32) DEFAULT NULL COMMENT '收藏加购成本',
  `collection_cart_count` bigint DEFAULT NULL COMMENT '收藏加购数',
  `collection_cart_rate` varchar(16) DEFAULT NULL COMMENT '收藏加购率',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_date_time` (`date_time`)
) ENGINE=InnoDB AUTO_INCREMENT=36 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='飞猪直通车';

DROP TABLE IF EXISTS `wanxiangtai`;
CREATE TABLE `wanxiangtai` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `date_time` date NOT NULL COMMENT 'Date 时间',
  `cost` varchar(32) DEFAULT NULL COMMENT 'Cost 花费',
  `imp` bigint DEFAULT NULL COMMENT 'IMP 观看量',
  `click` int DEFAULT NULL COMMENT 'Click 点击',
  `order_count` int DEFAULT NULL COMMENT 'Order 订单',
  `sales` varchar(32) DEFAULT NULL COMMENT 'Sales 销量',
  `shopping_cart` int DEFAULT NULL COMMENT 'ShoppingCart 加入购物车',
  `bookmark_product` int DEFAULT NULL COMMENT 'Bookmark-Product 宝贝收藏',
  `bookmark_store` int DEFAULT NULL COMMENT 'Bookmark-Store 店铺收藏',
  `ctr` varchar(16) DEFAULT NULL COMMENT 'CTR 点击率',
  `cpc` varchar(32) DEFAULT NULL COMMENT 'CPC 点击成本',
  `cpm` varchar(32) DEFAULT NULL COMMENT 'CPM 拉新成本',
  `roi` decimal(10,4) DEFAULT NULL COMMENT 'ROI 投资回报率',
  `cvr` varchar(16) DEFAULT NULL COMMENT 'CVR 点击转化率',
  `collection_cart_cost` varchar(32) DEFAULT NULL COMMENT '收藏加购成本',
  `collection_cart_count` int DEFAULT NULL COMMENT '收藏加购数',
  `collection_cart_rate` varchar(16) DEFAULT NULL COMMENT '收藏加购率',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_date_time` (`date_time`)
) ENGINE=InnoDB AUTO_INCREMENT=36 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='万相台';

DROP TABLE IF EXISTS `wanxiangtai_2`;
CREATE TABLE `wanxiangtai_2` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `date_time` date NOT NULL COMMENT '日期',
  `data_source` varchar(32) NOT NULL COMMENT '数据源',
  `cost` varchar(32) DEFAULT NULL COMMENT 'Cost 花费',
  `imp` bigint DEFAULT NULL COMMENT 'IMP 展示',
  `click` int DEFAULT NULL COMMENT 'Click 点击',
  `order_count` int DEFAULT NULL COMMENT 'Order 订单',
  `sales` varchar(32) DEFAULT NULL COMMENT 'Sales 销量',
  `shopping_cart` int DEFAULT NULL COMMENT 'ShoppingCart 加入购物车',
  `bookmark_product` int DEFAULT NULL COMMENT 'Bookmark-Product 宝贝收藏',
  `bookmark_store` int DEFAULT NULL COMMENT 'Bookmark-Store 店铺收藏',
  `ctr` varchar(16) DEFAULT NULL COMMENT 'CTR 点击率',
  `cpc` varchar(32) DEFAULT NULL COMMENT 'CPC 点击成本',
  `cpm` varchar(32) DEFAULT NULL COMMENT 'CPM 拉新成本（千次曝光）',
  `roi` decimal(10,4) DEFAULT NULL COMMENT 'ROI 投资回报率',
  `cvr` varchar(16) DEFAULT NULL COMMENT 'CVR 点击转化率',
  `collection_cart_cost` varchar(32) DEFAULT NULL COMMENT '收藏加购成本',
  `collection_cart_count` int DEFAULT NULL COMMENT '收藏加购数',
  `collection_cart_rate` varchar(16) DEFAULT NULL COMMENT '收藏加购率',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_date_time` (`date_time`),
  KEY `idx_date_source` (`date_time`,`data_source`)
) ENGINE=InnoDB AUTO_INCREMENT=176 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='万相台2';

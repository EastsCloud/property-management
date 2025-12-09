# 物业管理系统 Property Management
Based on Flask + SQLAlchemy

## 版本 Versions

### v-1.2

**Updates**: 业主模块扩展增强，包括收费、设备、工单，界面统一优化 Enhanced Owners modules, including Billing, Equipment, and Workorders; UI improved with more consistency
<br/>
**Fixes**: 修复中英文格式问题，修复日期时间处理问题 Bilingual format fixes, date and time processing fixes

### v-1.1
支持英语 Supports English

### v-1.0
基础功能模块 All fundamental modules

## 简介 Introduction

包含模块：业主、收费（收费项目、账单、缴费记录）、设备、工单、社区服务。
<br/>
Modules: Owners, Billing(Charge types, Invoices, Payments), Equipment, Work Orders, and Community

Available on https://property-management-blnu.onrender.com

## 快速开始 Quick Start
```bash
pip install -r requirements.txt
# initialize
flask --app app.py init-db
# run
flask --app app.py run
```
Access on http://127.0.0.1:5000

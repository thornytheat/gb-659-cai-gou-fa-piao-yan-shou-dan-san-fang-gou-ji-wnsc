# 数据字典

- run_id：规则版本与输入 SHA-256 前 12 位组成的稳定批次标识。
- line_no：从 1 开始的物理来源行号，不因隔离或排序改变。
- business_key：本项目声明的业务唯一键，始终按字符串存储。
- reason_code：隔离原因的稳定英文编码。
- accepted：进入业务计算的记录数。
- quarantined：保留证据但不参与业务计算的记录数。
- 数值：金额、税额、用量和权重使用 Decimal；对外序列化为字符串。
- 时间：存储为带偏移的 ISO 8601，分桶使用半开区间。
- 空值：缺失键、空串和业务哨兵分别记录。
- 幂等：完整输入字节与规则版本相同则复用 run_id，不新增结果。
- 装箱规格：主数据按货号维护多版 pack_code 与 pieces_per_box（Decimal 字符串）；批号缺失时按最小规格保守折算，区间上界按最大规格。
- 退货红票：conservative_pieces 为当天可冲税件数；covered_pieces 为累计已冲件数；initial_tax 为保守红票税额，added_tax 为批号补齐后累计追加税额；outstanding.pending_tax 为尚欠冲税额。
- 批号证据：return_batches 以（return_no, batch_no）为唯一键，登记该批实际 pack_code、箱数、折算件数与税额，重跑不产生第二条。


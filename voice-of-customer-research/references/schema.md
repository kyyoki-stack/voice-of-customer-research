# 数据契约

UTF-8 CSV，记录编号唯一，空值表示未知。`data/feedback.csv`必须是匿名化数据，不包含账号、头像、手机号和Cookie。HTML默认只展示`relevance=相关`记录；排除记录保留在CSV用于审计。

必填列：`sample_id,platform,quote,source_url,relevance,sentiment`。
相关记录还必须填写：`theme,usage_scene,pain_point,task_impact,evidence_strength,evidence_basis`。情绪枚举：正面/负面/混合/中性/未标注；证据：高/中/低；相关性：相关/不相关/待审核。

推荐列：`brand,model,published_at,software_version,identity_status,source_title,scope,batch,relevance_reason,display_quote,additional_quote,user_job,desired_outcome_inferred,primary_theme,limitations,live_recheck`。
- 日期为YYYY-MM-DD或空，不用采集日期代替发布日期；软件版本不能从帖子日期推断。
- `display_quote`、`additional_quote`必须来自同一匿名原文或已保存父评论上下文，缩短引用不可改写。
- `pain_point`可写“未表达明确痛点”；`task_impact`可写“信息不足”或“无明确负面影响”。
- `desired_outcome_inferred`属于AI推断。高证据需独立可核查的执行结果/复验；具体自述通常中，模糊短句/咨询通常低。
- 不拿情绪条数当故障率，不拿来源URL数当人数；主主题占比明确分母，多标签计数注明不可相加。

`data/needs.csv`列：`need_id,priority,need,theme_id,evidence_ids,reason,decision_type,insight,suggested_action,validation,confidence`。
`evidence_ids`为英文逗号分隔的相关记录ID，不能为空；priority仅P0/P1/P2。无证据的机会假设放报告待验证章节，不展示为证据支持的需求卡。

`data/source_audit.csv`列：`source_id,url,status,decision,sample_ids`。记录来源失败，不凭空计入采集样本。

人工/AI审阅需检查：主题是否准确、好评差评是否依据该条原声、任务影响是否超出原话、引文是否吻合、版本未知是否保持未知。完全重复与语义重复分别处理，注明删选规则；批次标注方法、模型/执行日期和人工修正写入数据报告。

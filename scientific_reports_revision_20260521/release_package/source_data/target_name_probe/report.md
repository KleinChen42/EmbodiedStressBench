# YCB True-Name Probe and Query Ablation

- Date tag: 20260521
- Probe output: `/data/openMythosBench_project/outputs/ycb_true_name_probe_20260521`
- Conditional ablation output: `/data/openMythosBench_project/outputs/open_vocab_true_name_query_ablation_ycb_clutter_20260521`

# ManiSkill YCB Target-Name Probe

- Rows: 20
- Errors: 0
- Non-generic target-label rows: 0
- Non-generic debug rows: 20
- True-name ablation allowed: True

Use the true-name query ablation only when non-generic names are visible in target labels or debug fields.
## Conditional ablation

Probe found non-generic target names/debug fields; running true-name query ablation.

## Audit correction

The conditional ablation was stopped after 85 partial JSON files because the probe showed target_label remained generic (	arget object) and the only non-generic debug value was ctor.name='ycb_object'. These partial files are ignored for manuscript claims. A true object-name prompt ablation remains not supported by the current ManiSkill adapter metadata.

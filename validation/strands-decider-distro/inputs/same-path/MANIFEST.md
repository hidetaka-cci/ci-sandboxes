# Same-path behavior vs cosmetic diffs

Every case keeps the same path and extension. Gold is assigned by a human
from the diff text, not from path-filtering.

| id | path | gold | why |
|----|------|------|-----|
| ts-comment-only | src/math.ts | cosmetic | comment added, code identical |
| ts-rename-only | src/math.ts | cosmetic | multiply renamed to product, body unchanged |
| ts-whitespace | src/math.ts | cosmetic | blank lines only |
| ts-multiply-bug | src/math.ts | behavioral | a*b becomes a+b |
| ts-guard-clause | src/math.ts | behavioral | new early return changes negatives |
| ts-increment-step | src/counter.ts | behavioral | +1 becomes +2 |
| yml-comment | .circleci/config.yml | cosmetic | comment only |
| yml-image-tag | .circleci/config.yml | scalar | cimg/node:22.16 -> 22.20, same job graph |
| yml-resource | .circleci/config.yml | scalar | resource_class small -> medium |
| yml-new-job | .circleci/config.yml | structural | new job + workflow edge |
| yml-drop-requires | .circleci/config.yml | structural | test no longer requires doctor |

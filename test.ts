export class FieldCollapse {
  field: number;
  inner_hits?: InnerHits | InnerHits[];
  max_concurrent_group_searches?: number;
  collapse?: FieldCollapse;
}

export class InnerHits {
  name?: string;
  size?: number;
  collapse?: FieldCollapse;
}


ulimit -l unlimited
MAX_LOCKED_MEMORY=unlimited

{% if service_fullname == "ElasticsearchData" %}

ES_HEAP_SIZE=|||{"Fn::FindInMap":["InstanceTypes", { "Ref" : "ElasticsearchDataInstanceType" }, "EsHeapSize"]}|||

{% elif service_fullname == "ElasticsearchMaster" %}

ES_HEAP_SIZE=|||{"Fn::FindInMap":["InstanceTypes", { "Ref" : "ElasticsearchMasterInstanceType" }, "EsHeapSize"]}|||

{% elif service_fullname == "ElasticsearchLb" %}

ES_HEAP_SIZE=|||{"Fn::FindInMap":["InstanceTypes", { "Ref" : "ElasticsearchLbInstanceType" }, "EsHeapSize"]}|||

{% endif %}

{% macro budget_tier(budget) %}
    case
        when budget < 25000000 then '1: <$25M'
        when budget < 50000000 then '2: $25M-$50M'
        when budget < 100000000 then '3: $50M-$100M'
        else '4: >$100M'
    end
{% endmacro %}
{% macro hash(cols) %}
    to_hex(
        md5(
            cast(
                concat(
                    {% for col in cols %}
                        coalesce(cast({{ col }} as string), ''){% if not loop.last %}, '-', {% endif %}
                    {% endfor %}
                ) as string
            )
        )
    )
{% endmacro %}
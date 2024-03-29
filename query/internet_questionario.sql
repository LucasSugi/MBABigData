select
	ano_prova as ano_prova_internet
	, case possui_internet
		when "Não." then "Não"
        else "Sim"
    end as internet
	, (percentile(nota_cn,0.5) + percentile(nota_ch,0.5) + percentile(nota_lc,0.5) + percentile(nota_mt,0.5) + percentile(nota_redacao,0.5)) / 5 as nota
from
	generic_sandbox.enem_fact
	join generic_sandbox.enem_dimensio_questionario_socio_economico on (enem_fact.id_questionario_socio_economico == enem_dimensio_questionario_socio_economico.id_questionario_socio_economico)
where
	Q025 is not null
group by
	1, 2
order by
	1, 2
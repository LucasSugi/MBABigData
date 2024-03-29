-- Consulta para usar como modelo
-- Substituir [dimensao] por uma outra dimensao que deseja-se analisar (elemento opcional se nao for utilizar remover a coluna e remover os numeros no group by e order by)
-- Substituir [questao] pela questao que deseja-se analisar
-- Também é possível alterar a métrica das notas
select
	ano_prova
	, [dimensao]
	, [questao]
	, (percentile(nota_cn,0.5) + percentile(nota_ch,0.5) + percentile(nota_lc,0.5) + percentile(nota_mt,0.5) + percentile(nota_redacao,0.5)) / 5 as nota
from
	generic_sandbox.enem_fact
	join generic_sandbox.enem_dimensio_questionario_socio_economico on (enem_fact.id_questionario_socio_economico == enem_dimensio_questionario_socio_economico.id_questionario_socio_economico)
group by
	1, 2, 3
order by
	1, 2, 3
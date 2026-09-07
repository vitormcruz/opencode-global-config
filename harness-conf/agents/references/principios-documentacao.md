# Princípios de Documentação

## Filosofia

1. **Código é documentação** — é o design da aplicação.
   Ferramentas que extraem conhecimento do código são
   preferíveis a docs manuais.
2. **Doc derivável não se armazena** — se pode ser gerada
   a partir do código, gere sob demanda.
3. **Doc é para público diferente do dev** — o dev prefere
   código. Doc vale quando contextualiza agentes, comunica
   com stakeholders, ou agrega abstração.
4. **Transformação justifica doc** — só manter doc separada
   se houver mudança de formato (texto→diagrama), abstração
   (código→visão condensada) ou sumarização (decisões
   dispersas→visão consolidada).
5. **Docs devem ser executáveis** — preferir especificações
   testáveis. Decisões arquiteturais viram fitness functions,
   critérios de aceitação viram specs executáveis.
6. **Brownfield é pragmático** — pode não comportar técnicas
   avançadas. Grafos de conhecimento (não-intrusivos) ajudam
   muito. Sugerir gradualismo.
7. **Doc atualizada ou nenhuma** — doc desatualizada é pior
   que ausência.

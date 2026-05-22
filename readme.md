# Task Scheduling Simulator

Projeto para simular escalonamento de tarefas em DAGs usando diferentes algoritmos.

## Como rodar

O simulador principal está no arquivo `main.py`.

Se o ambiente virtual `ve` já estiver disponível, rode:

```bash
./ve/bin/python main.py
```

Se preferir usar o Python do sistema, primeiro ative o ambiente virtual e depois execute:

```bash
source ve/bin/activate
python main.py
```

## Opções úteis

Você pode escolher o escalonador com `--scheduler`:

```bash
./ve/bin/python main.py --scheduler FIFO
./ve/bin/python main.py --scheduler HEFT
./ve/bin/python main.py --scheduler PEFT
```

Para trocar o DAG de entrada, use `--dag-path`:

```bash
./ve/bin/python main.py --dag-path dag-instances/wfcommons/blast-chameleon-large-002.json
./ve/bin/python main.py --dag-path /caminho/absoluto/para/seu-dag.json
```

Outros parâmetros disponíveis:

- `--visualize`: mostra uma visualização das tarefas e dos processadores enquanto o simulador executa.
- `--log-level`: define o nível de log. Os valores aceitos são `CRITICAL`, `ERROR`, `WARNING`, `INFO` e `DEBUG`.
- `--silence`: desliga os logs do escalonador.

## Exemplo

```bash
./ve/bin/python main.py --scheduler HEFT --visualize --log-level INFO
```
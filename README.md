# Bot de Inspeção de Lotes Diários

## Resumo do Projeto
Este projeto é uma automação desenvolvida em Python para realizar a triagem e validação da planilha de inspeção diária do controle de qualidade. O bot atua como um filtro de governança inicial, aplicando regras de negócio (RN01 a RN07) para automatizar o trabalho braçal. 

## Pré-requisitos
* Python 3.11+
* Gerenciador de pacotes `pip`

## Instalação e Configuração

1. **Acesse a pasta do projeto:**
   ```bash
   cd caminho/para/o/projeto
   ```

2. **Crie e ative um ambiente virtual:**

   No Windows:
   ```bash
   python -m venv .venv
   venv\Scripts\activate
   ```

   No Linux/Ubuntu:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instale as dependências do projeto:** O projeto requer bibliotecas para manipulação de dados e testes (como pandas, openpyxl e pytest). Instale todas rodando:
   ```bash
   pip install -r requirements.txt
   ```

## Como Executar

Para iniciar o bot e processar a planilha do dia:

```bash
python src/main.py
```

Para rodar a suíte de testes unitários e garantir que as validações (RN01-RN07) estão funcionando corretamente:

```bash
pytest
```


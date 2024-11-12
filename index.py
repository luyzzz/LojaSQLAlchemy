from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, func
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from colorama import Fore, Style, init

# Inicializar colorama
init(autoreset=True)

Base = declarative_base()


class Cliente(Base):
    __tablename__ = 'clientes'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    email = Column(String, nullable=False)

    pedidos = relationship('Pedido', back_populates='cliente')


class Produto(Base):
    __tablename__ = 'produtos'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    preco = Column(Float, nullable=False)
    estoque = Column(Integer, nullable=False)


class Pedido(Base):
    __tablename__ = 'pedidos'
    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id'), nullable=False)
    produto_id = Column(Integer, ForeignKey('produtos.id'), nullable=False)
    quantidade = Column(Integer, nullable=False)

    cliente = relationship('Cliente', back_populates='pedidos')
    produto = relationship('Produto')


class CompraTotalizada(Base):
    __tablename__ = 'compra_totalizadas'
    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id'), nullable=False)
    valor_total = Column(Float, nullable=False)


def adicionar_cliente(session, nome, email):
    cliente = Cliente(nome=nome, email=email)
    session.add(cliente)
    session.commit()
    print(f"Cliente '{nome}' adicionado com sucesso.")


def adicionar_produto(session, nome, preco, estoque):
    produto = Produto(nome=nome, preco=preco, estoque=estoque)
    session.add(produto)
    session.commit()
    print(f"Produto '{nome}' adicionado com sucesso.")


def verificar_estoque(session, produto_id, quantidade):
    produto = session.query(Produto).filter_by(id=produto_id).first()
    return produto and produto.estoque >= quantidade


def fazer_pedido(session, cliente_id, produto_id, quantidade):
    produto = session.query(Produto).filter_by(id=produto_id).first()
    if verificar_estoque(session, produto_id, quantidade):
        total = produto.preco * quantidade
        pedido = Pedido(cliente_id=cliente_id, produto_id=produto_id, quantidade=quantidade)
        produto.estoque -= quantidade
        session.add(pedido)
        session.commit()
        print(Fore.GREEN + f"Pedido realizado com sucesso. Valor total: R$ {total:.2f}")

        # Atualizar o valor total do cliente após o pedido
        calcular_valor_total(session, cliente_id)
    else:
        print("Estoque insuficiente para realizar o pedido.")


def calcular_valor_total(session, cliente_id):
    # Calcular o valor total dos pedidos do cliente
    total = session.query(func.sum(Pedido.quantidade * Produto.preco)). \
        join(Produto, Pedido.produto_id == Produto.id). \
        filter(Pedido.cliente_id == cliente_id).scalar()

    if total is None:
        total = 0.0

    # Adicionar ou atualizar a entrada em CompraTotalizada
    compra = session.query(CompraTotalizada).filter_by(cliente_id=cliente_id).first()
    if compra:
        compra.valor_total = total
    else:
        compra = CompraTotalizada(cliente_id=cliente_id, valor_total=total)
        session.add(compra)

    session.commit()
    print(Fore.GREEN + f"Valor total dos pedidos do cliente ID {cliente_id}: R$ {total:.2f}")


def listar_produtos(session):
    produtos = session.query(Produto).all()
    for produto in produtos:
        print(f"{produto.id}: {produto.nome} - R$ {produto.preco} - Estoque: {produto.estoque}")


def listar_pedidos_cliente(session, cliente_id):
    pedidos = session.query(Pedido).filter_by(cliente_id=cliente_id).all()
    if not pedidos:
        print(Fore.RED + "Você não tem pedidos.")
    else:
        for pedido in pedidos:
            produto = session.query(Produto).filter_by(id=pedido.produto_id).first()
            print(f"Pedido ID: {pedido.id} - Produto: {produto.nome} - Quantidade: {pedido.quantidade}")


def realizar_compra(session, cliente_id):
    pedidos = session.query(Pedido).filter_by(cliente_id=cliente_id).all()
    valor_total = 0.0

    print("Resumo dos pedidos:")
    for pedido in pedidos:
        produto = session.query(Produto).filter_by(id=pedido.produto_id).first()
        subtotal = produto.preco * pedido.quantidade
        valor_total += subtotal
        print(f"{produto.nome} - Quantidade: {pedido.quantidade} - Subtotal: R$ {subtotal:.2f}")

    print(Fore.GREEN + f"\nValor total da compra: R$ {valor_total:.2f}")


def tirar_pedido(session, cliente_id):
    print("Pedidos do cliente:")
    listar_pedidos_cliente(session, cliente_id)

    pedido_id = int(input("Digite o ID do pedido que deseja ajustar ou remover: "))
    pedido = session.query(Pedido).filter_by(id=pedido_id, cliente_id=cliente_id).first()

    if pedido:
        produto = session.query(Produto).filter_by(id=pedido.produto_id).first()
        print(f"Pedido selecionado: {produto.nome} - Quantidade: {pedido.quantidade}")

        quantidade_para_remover = int(input("Digite a quantidade que deseja remover: "))

        if quantidade_para_remover >= pedido.quantidade:
            produto.estoque += pedido.quantidade  # Devolve o estoque total do pedido
            session.delete(pedido)  # Remove o pedido completamente
            session.commit()
            print(Fore.GREEN + "Pedido removido com sucesso.")
        else:
            pedido.quantidade -= quantidade_para_remover
            produto.estoque += quantidade_para_remover  # Devolve apenas a quantidade ajustada ao estoque
            session.commit()
            print(f"Pedido ajustado. Nova quantidade: {pedido.quantidade}")

        # Atualizar o valor total do cliente após ajuste ou remoção de pedido
        calcular_valor_total(session, cliente_id)
    else:
        print("Pedido não encontrado.")


def interface_compra(session):
    print(Fore.BLUE + "Bem-vindo ao sistema de compras!")
    cliente_id = int(input("Digite o ID do cliente: "))

    while True:
        print("\n1. Listar produtos\n2. Fazer pedido\n3. Ver pedidos\n4. Realizar compra\n5. Remover pedido\n6. Sair")
        escolha = input("Escolha uma opção: ")

        if escolha == '1':
            listar_produtos(session)

        elif escolha == '2':
            produto_id = int(input("Digite o ID do produto: "))
            quantidade = int(input("Digite a quantidade: "))
            fazer_pedido(session, cliente_id, produto_id, quantidade)

        elif escolha == '3':
            listar_pedidos_cliente(session, cliente_id)

        elif escolha == '4':
            realizar_compra(session, cliente_id)

        elif escolha == '5':
            tirar_pedido(session, cliente_id)

        elif escolha == '6':
            break


# Configuração do banco de dados e sessão
engine = create_engine('sqlite:///loja.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Adicionando exemplos de clientes e produtos
if not session.query(Cliente).first():
    adicionar_cliente(session, 'João Silva', 'joao.silva@example.com')
    adicionar_cliente(session, 'Maria Oliveira', 'maria.oliveira@example.com')

if not session.query(Produto).first():
    adicionar_produto(session, 'Laptop', 3500.0, 10)
    adicionar_produto(session, 'Smartphone', 1500.0, 20)
    adicionar_produto(session, 'Teclado', 150.0, 50)

# Interface de compra
interface_compra(session)

"""Starter catalogs for food businesses. Prices are suggestions, not local quotes."""
from decimal import Decimal
from app.models import Product

# Prices are initial editable suggestions in BRL. Real prices vary by city, ingredients,
# portion size, packaging, delivery fees, taxes and marketplace commission.
CATALOGS = {
    "hamburgueria": [
        ("Hambúrguer Simples", "Pão, hambúrguer, maionese e molho da casa.", "Hambúrgueres", "12.90"),
        ("X-Burger", "Pão, hambúrguer, queijo e maionese.", "Hambúrgueres", "16.90"),
        ("X-Salada", "Pão, hambúrguer, queijo, alface, tomate e maionese.", "Hambúrgueres", "18.90"),
        ("X-Egg", "Pão, hambúrguer, queijo, ovo e maionese.", "Hambúrgueres", "19.90"),
        ("X-Bacon", "Pão, hambúrguer, queijo, bacon e maionese.", "Hambúrgueres", "22.90"),
        ("X-Calabresa", "Pão, hambúrguer, queijo e calabresa.", "Hambúrgueres", "21.90"),
        ("X-Frango", "Pão, filé de frango, queijo e maionese.", "Hambúrgueres", "20.90"),
        ("X-Frango Salada", "Pão, frango, queijo, alface, tomate e molho.", "Hambúrgueres", "22.90"),
        ("X-Tudo", "Pão, hambúrguer, queijo, presunto, ovo, bacon e salada.", "Hambúrgueres", "26.90"),
        ("X-Tudo Duplo", "Pão, dois hambúrgueres, queijo, ovo, bacon e salada.", "Hambúrgueres", "32.90"),
        ("Cheeseburger Duplo", "Pão, dois hambúrgueres, queijo e molho da casa.", "Hambúrgueres", "27.90"),
        ("Burger Artesanal da Casa", "Pão brioche, burger artesanal, queijo e molho da casa.", "Artesanais", "29.90"),
        ("Burger Artesanal Bacon", "Pão brioche, burger artesanal, queijo, bacon e molho.", "Artesanais", "34.90"),
        ("Burger Vegetariano", "Pão, burger vegetariano, queijo e salada.", "Artesanais", "27.90"),
        ("Hot Dog Tradicional", "Pão, salsicha, molho e batata palha.", "Hot dogs", "12.90"),
        ("Hot Dog Completo", "Pão, salsicha, molho, queijo, milho e batata palha.", "Hot dogs", "17.90"),
        ("Batata Frita Pequena", "Porção individual.", "Porções", "12.90"),
        ("Batata Frita com Cheddar e Bacon", "Batata frita, cheddar e bacon.", "Porções", "24.90"),
        ("Refrigerante Lata", "Lata 350 ml. Escolha o sabor disponível.", "Bebidas", "6.00"),
        ("Água Mineral", "Garrafa 500 ml.", "Bebidas", "3.50"),
        ("Combo X-Burger", "X-burger, batata pequena e refrigerante lata.", "Combos", "27.90"),
        ("Combo X-Bacon", "X-bacon, batata pequena e refrigerante lata.", "Combos", "33.90"),
    ],
    "pizzaria": [
        ("Pizza Mussarela", "Pizza tradicional de mussarela.", "Pizzas", "39.90"),
        ("Pizza Calabresa", "Calabresa, cebola e mussarela.", "Pizzas", "42.90"),
        ("Pizza Presunto e Queijo", "Presunto, mussarela e molho de tomate.", "Pizzas", "42.90"),
        ("Pizza Portuguesa", "Presunto, ovo, cebola, ervilha e mussarela.", "Pizzas", "47.90"),
        ("Pizza Frango com Catupiry", "Frango desfiado e requeijão tipo catupiry.", "Pizzas", "49.90"),
        ("Pizza Quatro Queijos", "Mix de queijos.", "Pizzas", "49.90"),
        ("Pizza Bacon", "Bacon, mussarela e molho de tomate.", "Pizzas", "47.90"),
        ("Pizza Chocolate", "Chocolate ao leite.", "Pizzas doces", "44.90"),
        ("Refrigerante 2 L", "Escolha o sabor disponível.", "Bebidas", "12.00"),
        ("Refrigerante Lata", "Lata 350 ml.", "Bebidas", "6.00"),
    ],
    "lanchonete": [
        ("Misto Quente", "Pão, presunto e queijo.", "Lanches", "10.90"),
        ("X-Burger", "Pão, hambúrguer, queijo e molho.", "Lanches", "16.90"),
        ("X-Salada", "Pão, hambúrguer, queijo, alface e tomate.", "Lanches", "18.90"),
        ("X-Egg", "Pão, hambúrguer, queijo e ovo.", "Lanches", "19.90"),
        ("X-Bacon", "Pão, hambúrguer, queijo e bacon.", "Lanches", "22.90"),
        ("X-Tudo", "Pão, hambúrguer, queijo, presunto, ovo, bacon e salada.", "Lanches", "26.90"),
        ("Hot Dog", "Pão, salsicha, molho e batata palha.", "Lanches", "12.90"),
        ("Pastel de Queijo", "Pastel frito recheado com queijo.", "Pastéis", "10.00"),
        ("Pastel de Carne", "Pastel frito recheado com carne.", "Pastéis", "10.00"),
        ("Batata Frita", "Porção de batatas fritas.", "Porções", "16.90"),
        ("Açaí 300 ml", "Açaí com acompanhamentos básicos.", "Sobremesas", "16.90"),
        ("Refrigerante Lata", "Lata 350 ml.", "Bebidas", "6.00"),
        ("Suco Natural", "Copo 300 ml. Consulte sabores.", "Bebidas", "8.00"),
    ],
    "restaurante": [
        ("Prato Feito de Frango", "Arroz, feijão, frango e acompanhamento.", "Pratos feitos", "22.90"),
        ("Prato Feito de Carne", "Arroz, feijão, carne e acompanhamento.", "Pratos feitos", "26.90"),
        ("Prato Feito de Bife Acebolado", "Arroz, feijão, bife acebolado e acompanhamento.", "Pratos feitos", "27.90"),
        ("Prato Feito de Linguiça", "Arroz, feijão, linguiça e acompanhamento.", "Pratos feitos", "21.90"),
        ("Marmita Pequena", "Refeição do dia em embalagem pequena.", "Marmitas", "18.90"),
        ("Marmita Média", "Refeição do dia em embalagem média.", "Marmitas", "23.90"),
        ("Marmita Grande", "Refeição do dia em embalagem grande.", "Marmitas", "28.90"),
        ("Salada da Casa", "Salada fresca com ingredientes do dia.", "Acompanhamentos", "12.90"),
        ("Porção de Batata Frita", "Porção para compartilhar.", "Acompanhamentos", "16.90"),
        ("Refrigerante Lata", "Lata 350 ml.", "Bebidas", "6.00"),
        ("Suco Natural", "Copo 300 ml. Consulte sabores.", "Bebidas", "8.00"),
        ("Água Mineral", "Garrafa 500 ml.", "Bebidas", "3.50"),
    ],
    "doceria": [
        ("Brigadeiro", "Unidade.", "Doces", "3.50"),
        ("Beijinho", "Unidade.", "Doces", "3.50"),
        ("Brownie", "Unidade.", "Doces", "8.00"),
        ("Fatia de Bolo", "Fatia do sabor do dia.", "Bolos", "10.00"),
        ("Bolo de Cenoura com Chocolate", "Fatia individual.", "Bolos", "11.00"),
        ("Pudim", "Fatia individual.", "Sobremesas", "9.00"),
        ("Cone Trufado", "Unidade. Consulte sabores.", "Doces", "8.00"),
        ("Caixa com 4 Brigadeiros", "Caixa com quatro unidades.", "Combos", "13.00"),
        ("Café", "Xícara de café.", "Bebidas", "5.00"),
    ],
    "cafeteria": [
        ("Café Expresso", "Dose de café expresso.", "Cafés", "6.00"),
        ("Café com Leite", "Café com leite quente.", "Cafés", "7.00"),
        ("Cappuccino", "Cappuccino tradicional.", "Cafés", "10.00"),
        ("Chocolate Quente", "Xícara de chocolate quente.", "Bebidas", "10.00"),
        ("Pão de Queijo", "Porção com 2 unidades.", "Salgados", "8.00"),
        ("Croissant", "Unidade.", "Salgados", "10.00"),
        ("Misto Quente", "Pão, presunto e queijo.", "Lanches", "12.00"),
        ("Sanduíche Natural", "Pão integral, frango e salada.", "Lanches", "16.00"),
        ("Fatia de Bolo", "Fatia do sabor do dia.", "Doces", "10.00"),
        ("Suco Natural", "Copo 300 ml.", "Bebidas", "8.00"),
    ],
    "outros_alimentos": [
        ("Produto do Dia", "Edite o nome e a descrição deste item.", "Destaques", "15.00"),
        ("Combo da Casa", "Edite os itens incluídos neste combo.", "Combos", "25.00"),
        ("Porção Individual", "Edite a descrição e o tamanho da porção.", "Porções", "12.00"),
        ("Bebida Lata", "Lata 350 ml. Edite conforme as marcas disponíveis.", "Bebidas", "6.00"),
    ],
}

FOOD_TYPES = set(CATALOGS)


def seed_catalog(tenant, business_type):
    """Create a starter menu once for a newly registered food tenant."""
    items = CATALOGS.get(business_type)
    if not items:
        return 0
    for name, description, category, price in items:
        db_product = Product(
            tenant_id=tenant.id,
            name=name,
            description=description,
            category=category,
            price=Decimal(price),
            is_available=True,
        )
        from app import db
        db.session.add(db_product)
    return len(items)

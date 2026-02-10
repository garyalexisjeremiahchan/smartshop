"""
System prompts and OpenAI tool/function definitions for the shopping assistant.
"""

SYSTEM_PROMPT = """You are a helpful shopping assistant for an online e-commerce store. Your role is to help customers find products, answer questions about specifications and availability, provide recommendations, and assist with their shopping journey.

CRITICAL RULES:
1. You MUST use the provided tools for ALL factual information about products, prices, stock, specifications, reviews, and availability.
2. NEVER guess or make up product information, prices, stock levels, or specifications.
3. NEVER show products to users without first calling search_products or another product tool - you must have actual product data from the database.
4. If a tool returns no results or empty data, acknowledge this honestly and suggest alternative searches or actions.
5. Keep responses concise, friendly, and action-oriented (2-4 sentences typically).
6. When recommending products, show 3-5 options maximum and explain why they match the user's needs.
7. Always ask one follow-up question to refine preferences when appropriate.
8. Do not expose internal-only information like cost, supplier details, or admin flags.
9. Be transparent about limitations - if you can't find something, say so and help the user refine their search.
10. CRITICAL FOR CART: You can ONLY add products to cart if you have their product_id from a search_products or get_product_details call. NEVER guess product IDs. If you don't have the product_id from a tool call, search for the product first.
11. When users ask you to create an outfit or suggest products, you MUST call search_products for each category/item type to get real products from the database.
12. EXTREMELY IMPORTANT - PRODUCT IDS: When calling add_to_cart, you MUST use the EXACT product_id value returned from search_products or get_product_details. Product IDs are NOT sequential (not 1, 2, 3, 4). They are specific numbers like 1768, 1767, 1766. ALWAYS use the actual 'id' field from the product data you received from the tools. NEVER make up or guess product IDs.
13. CRITICAL WORKFLOW - ADDING TO CART: When you call search_products and get results, each product in the response has an 'id' field. You MUST remember these exact IDs. When the user asks to add products to cart, call add_to_cart with those EXACT IDs you received. DO NOT use sequential numbers like 1, 2, 3 or random numbers like 1234, 5678. Use the REAL IDs from the search results.

SPECIAL BEHAVIORS:
- When users ask to "show me categories" or "browse categories", use get_categories tool and then tell them: "You can browse all our categories here: [Categories Page](/categories/)"
- When listing individual categories, format each as a markdown link using the EXACT URL from the tool result - DO NOT add any domain or protocol
- When users ask for "popular products", "best sellers", or "top selling products", use the get_top_selling_products tool to show our current bestsellers
- Always include clickable links when directing users to specific pages
- CRITICAL: Use ONLY relative paths for all links (e.g., /category/electronics/ NOT https://yourstore.com/category/electronics/)
- NEVER add domains, protocols (http/https), or hostnames to URLs - only use the relative paths provided by the tools
- When users ask to add a product to cart, buy something, or purchase an item, use the add_to_cart tool with the correct product_id and quantity
- After successfully adding to cart, tell users they can view their cart at [here](/cart/)
- CRITICAL: ADDING MULTIPLE ITEMS TO CART - Step by step process:
  1. When you show products from search_products, REMEMBER the exact 'id' field for each product
  2. When user asks to "add all to cart", call add_to_cart ONCE for EACH product
  3. Use the EXACT product IDs you just received from search_products
  4. EXAMPLE: If search_products returned: [{id: 1523, name: "Travel Bottles"}, {id: 1687, name: "Money Belt"}, {id: 1442, name: "Duffle Bag"}]
     Then call: add_to_cart(1523), add_to_cart(1687), add_to_cart(1442)
     NEVER call: add_to_cart(1), add_to_cart(2), add_to_cart(3) or add_to_cart(1234), add_to_cart(5678)
- SEARCH STRATEGY: When searching for specific items (e.g., "beach shirt", "swim trunks"), if you get no results, try broader search terms (e.g., "shirt", "shorts") or search by category. Use general terms rather than overly specific ones. For outfit recommendations, search by category or general product types.

RESPONSE STYLE:
- Friendly and conversational but professional
- Use bullet points for clarity when listing multiple items
- Highlight key differentiators (price, features, ratings) when comparing products
- Provide clear next steps (e.g., "Would you like to see more options?" or "Should I add this to your cart?")
- When appropriate, include navigation links to help users browse (format: [Link Text](URL))

CONTEXT AWARENESS:
- You receive page context (current product, category, search query, cart status) with each message
- Use this context to provide more relevant assistance
- Reference what the user is currently viewing when helpful
- CRITICAL: When the user is on a product detail page (page_type="product_detail") and asks about "this product" or "tell me about this product", ALWAYS use get_product_details with the provided product_id from the context
- When user says "this product" or similar phrases, they are referring to the product_id in the context - immediately call get_product_details with that ID

Remember: Your credibility depends on accuracy. Always use tools, never hallucinate data."""


# OpenAI Function/Tool Definitions
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Search for products in the catalog. Use this to find products based on keywords, filters, and sorting preferences. Returns a list of matching products with basic information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search keywords or product name to search for"
                    },
                    "category": {
                        "type": "string",
                        "description": "Filter by category slug (e.g., 'electronics', 'clothing')"
                    },
                    "min_price": {
                        "type": "number",
                        "description": "Minimum price filter"
                    },
                    "max_price": {
                        "type": "number",
                        "description": "Maximum price filter"
                    },
                    "min_rating": {
                        "type": "number",
                        "description": "Minimum average rating (1-5)"
                    },
                    "in_stock_only": {
                        "type": "boolean",
                        "description": "Only return products that are in stock",
                        "default": False
                    },
                    "sort": {
                        "type": "string",
                        "enum": ["popular", "latest", "price_low_high", "price_high_low", "rating"],
                        "description": "How to sort the results"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (max 10)",
                        "default": 5
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_details",
            "description": "Get detailed information about a specific product including full description, variants, images, and current price. Use this when the user asks about a specific product or you need complete product information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer",
                        "description": "The ID of the product to get details for"
                    }
                },
                "required": ["product_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_specs",
            "description": "Get detailed specifications for a specific product. Use this when users ask about technical details, features, dimensions, materials, or other specifications.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer",
                        "description": "The ID of the product to get specifications for"
                    }
                },
                "required": ["product_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_availability",
            "description": "Check current stock availability for a specific product. Returns current stock level and stock status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer",
                        "description": "The ID of the product to check availability for"
                    }
                },
                "required": ["product_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_reviews_summary",
            "description": "Get a summary of customer reviews for a product, including average rating, review count, pros and cons, and overall sentiment. Use this when users ask about product quality, customer opinions, or experiences.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer",
                        "description": "The ID of the product to get review summary for"
                    }
                },
                "required": ["product_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_similar_products",
            "description": "Find products similar to a given product, based on category and attributes. Useful for showing alternatives or related items.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer",
                        "description": "The ID of the product to find similar products for"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of similar products to return (max 5)",
                        "default": 3
                    }
                },
                "required": ["product_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_categories",
            "description": "Get a list of all available product categories. Use this to help users browse or when they ask what types of products are available. When users ask to 'show me categories', direct them to browse the category page at /categories/.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_selling_products",
            "description": "Get the top selling / most popular products based on sales. Use this when users ask for 'popular products', 'best sellers', 'top products', or 'what's selling well'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of products to return (max 10)",
                        "default": 10
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_cart",
            "description": "Add a product to the user's shopping cart. Use this when the user explicitly asks to add a product to their cart, buy a product, or purchase something. ONLY call this after the user has confirmed they want to add the specific product.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "integer",
                        "description": "The ID of the product to add to cart"
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Number of items to add (default: 1)",
                        "default": 1
                    }
                },
                "required": ["product_id"]
            }
        }
    }
]

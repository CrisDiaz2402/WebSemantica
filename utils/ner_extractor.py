import re
import unicodedata
import gc
import psutil
import os
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NERExtractor:
    """Memory-optimized Named Entity Extractor using pre-trained models"""

    def __init__(self, model_name: str = "lightweight"):
        self.model_name = model_name
        self.primary_model = None
        self.model_type = None
        self.processed_count = 0
        self.memory_threshold = 80  # Percentage of memory usage to trigger cleanup
        
        # Initialize only the lightest available model
        self._initialize_lightweight_model()
        
        # Entity mapping for consistency across different models
        self.entity_mapping = {
            # spaCy labels
            'PERSON': 'Person',
            'PER': 'Person',
            'ORG': 'Organization', 
            'ORGANIZATION': 'Organization',
            'GPE': 'Location',
            'LOC': 'Location',
            'LOCATION': 'Location',
            'DATE': 'Date',
            'TIME': 'Time',
            'MONEY': 'Money',
            'QUANTITY': 'Quantity',
            'PRODUCT': 'Product',
            'MISC': 'Miscellaneous',
            'WORK_OF_ART': 'Product',
            'EVENT': 'Event',
            'FAC': 'Location',
            'LANGUAGE': 'Language',
            'LAW': 'Law',
            'NORP': 'Group',
            'ORDINAL': 'Number',
            'PERCENT': 'Percentage',
            'CARDINAL': 'Number',
            
            # NLTK labels
            'ORGANIZATION': 'Organization',
            'FACILITY': 'Location',
            'GSP': 'Location'
        }

    def _get_memory_usage(self) -> float:
        """Get current memory usage percentage"""
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            return memory_percent
        except:
            return 0

    def _cleanup_memory(self):
        """Force garbage collection and memory cleanup"""
        gc.collect()
        
        # If using spaCy, clear its cache
        if self.model_type == 'spacy' and self.primary_model:
            try:
                # Clear spaCy's internal caches
                self.primary_model.vocab.strings._reset_and_load()
            except:
                pass

    def _initialize_lightweight_model(self):
        """Initialize only the lightest available NER model"""
        models_tried = []
        
        # 1. Try NLTK first (lightest)
        try:
            import nltk
            from nltk import ne_chunk, pos_tag, word_tokenize
            
            # Download required data quietly
            required_data = ['punkt', 'averaged_perceptron_tagger', 'maxent_ne_chunker', 'words']
            for data in required_data:
                try:
                    nltk.data.find(f'tokenizers/{data}' if data == 'punkt' else 
                                 f'taggers/{data}' if 'tagger' in data else
                                 f'chunkers/{data}' if 'chunker' in data else
                                 f'corpora/{data}')
                except LookupError:
                    nltk.download(data, quiet=True)
            
            self.primary_model = None  # NLTK doesn't need to store a model
            self.model_type = 'nltk'
            models_tried.append("NLTK (Basic NER)")
            logger.info("✓ NLTK model initialized (lightest option)")
            return
        except ImportError:
            logger.warning("✗ NLTK not available")

        # 2. Try spaCy with small model (if NLTK failed)
        try:
            import spacy
            try:
                # Load with minimal components to save memory
                nlp = spacy.load("en_core_web_sm", disable=["parser", "tagger", "lemmatizer", "textcat"])
                self.primary_model = nlp
                self.model_type = 'spacy'
                models_tried.append("spaCy (en_core_web_sm - minimal)")
                logger.info("✓ spaCy small model loaded with minimal components")
                return
            except OSError:
                try:
                    # Try to download if not available
                    import subprocess
                    import sys
                    subprocess.check_call([sys.executable, '-m', 'spacy', 'download', 'en_core_web_sm'], 
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    nlp = spacy.load("en_core_web_sm", disable=["parser", "tagger", "lemmatizer", "textcat"])
                    self.primary_model = nlp
                    self.model_type = 'spacy'
                    models_tried.append("spaCy (en_core_web_sm - downloaded)")
                    logger.info("✓ spaCy small model downloaded and loaded")
                    return
                except:
                    logger.warning("✗ Could not load spaCy small model")
        except ImportError:
            logger.warning("✗ spaCy not available")

        # 3. Fallback to regex-based extraction
        self.primary_model = None
        self.model_type = 'regex'
        models_tried.append("Regex-based (fallback)")
        logger.warning("Using regex-based fallback - limited accuracy")

        # Log initialization results
        if models_tried:
            logger.info(f"NER model initialized: {models_tried[-1]}")
        else:
            raise RuntimeError("No NER models available. Please install nltk or spacy.")

    def normalize_text(self, text: str) -> str:
        """Lightweight text normalization"""
        if not text:
            return ""
        
        # Basic normalization without heavy processing
        text = re.sub(r'\s+', ' ', text.strip())
        return text

    def extract_with_spacy(self, text: str) -> List[Dict[str, any]]:
        """Extract entities using spaCy with memory optimization"""
        entities = []
        try:
            # Process in smaller chunks to avoid memory issues
            max_length = 1000  # Reduced chunk size
            if len(text) > max_length:
                chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
                offset = 0
                for chunk in chunks:
                    doc = self.primary_model(chunk)
                    for ent in doc.ents:
                        entity_type = self.entity_mapping.get(ent.label_, ent.label_)
                        entities.append({
                            'text': ent.text,
                            'label': entity_type,
                            'start': ent.start_char + offset,
                            'end': ent.end_char + offset,
                            'confidence': 0.9,
                            'method': 'spacy'
                        })
                    offset += len(chunk)
                    # Clear doc from memory
                    del doc
            else:
                doc = self.primary_model(text)
                for ent in doc.ents:
                    entity_type = self.entity_mapping.get(ent.label_, ent.label_)
                    entities.append({
                        'text': ent.text,
                        'label': entity_type,
                        'start': ent.start_char,
                        'end': ent.end_char,
                        'confidence': 0.9,
                        'method': 'spacy'
                    })
                # Clear doc from memory
                del doc
                
        except Exception as e:
            logger.error(f"spaCy extraction error: {e}")
            # Force cleanup on error
            self._cleanup_memory()
        
        return entities

    def extract_with_nltk(self, text: str) -> List[Dict[str, any]]:
        """Extract entities using NLTK (memory efficient)"""
        entities = []
        try:
            import nltk
            from nltk import ne_chunk, pos_tag, word_tokenize
            
            # Process in smaller chunks for large texts
            max_length = 2000
            if len(text) > max_length:
                chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
                offset = 0
                for chunk in chunks:
                    chunk_entities = self._process_nltk_chunk(chunk, offset)
                    entities.extend(chunk_entities)
                    offset += len(chunk)
            else:
                entities = self._process_nltk_chunk(text, 0)
                
        except Exception as e:
            logger.error(f"NLTK extraction error: {e}")
        
        return entities

    def _process_nltk_chunk(self, text: str, offset: int) -> List[Dict[str, any]]:
        """Process a single chunk with NLTK"""
        entities = []
        try:
            import nltk
            from nltk import ne_chunk, pos_tag, word_tokenize
            
            tokens = word_tokenize(text)
            pos_tags = pos_tag(tokens)
            chunks = ne_chunk(pos_tags, binary=False)
            
            current_pos = 0
            for chunk in chunks:
                if hasattr(chunk, 'label'):
                    entity_text = ' '.join([token for token, pos in chunk.leaves()])
                    entity_type = self.entity_mapping.get(chunk.label(), chunk.label())
                    
                    # Find position in original text
                    start_pos = text.find(entity_text, current_pos)
                    if start_pos != -1:
                        entities.append({
                            'text': entity_text,
                            'label': entity_type,
                            'start': start_pos + offset,
                            'end': start_pos + len(entity_text) + offset,
                            'confidence': 0.7,
                            'method': 'nltk'
                        })
                        current_pos = start_pos + len(entity_text)
        except Exception as e:
            logger.error(f"NLTK chunk processing error: {e}")
        
        return entities

    def extract_with_regex(self, text: str) -> List[Dict[str, any]]:
        """Fallback regex-based entity extraction"""
        entities = []
        
        # Simple patterns for basic entity recognition
        patterns = {
            'Person': r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',
            'Organization': r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Inc|Corp|Ltd|LLC|Company|Co)\b',
            'Location': r'\b(?:New York|Los Angeles|Chicago|Houston|Phoenix|Philadelphia|San Antonio|San Diego|Dallas|San Jose|Austin|Jacksonville|Fort Worth|Columbus|Charlotte|San Francisco|Indianapolis|Seattle|Denver|Washington|Boston)\b',
            'Money': r'\$\d+(?:,\d{3})*(?:\.\d{2})?',
            'Date': r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b'
        }
        
        for entity_type, pattern in patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append({
                    'text': match.group(),
                    'label': entity_type,
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.6,
                    'method': 'regex'
                })
        
        return entities

    def extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract entities using the available model with memory management"""
        if not text:
            return []
        
        # Check memory usage and cleanup if needed
        self.processed_count += 1
        if self.processed_count % 50 == 0:  # Check every 50 documents
            memory_usage = self._get_memory_usage()
            if memory_usage > self.memory_threshold:
                logger.info(f"Memory usage at {memory_usage:.1f}%, performing cleanup...")
                self._cleanup_memory()
        
        # Normalize text (lightweight)
        normalized_text = self.normalize_text(text)
        
        entities = []
        
        # Use the appropriate extraction method
        try:
            if self.model_type == 'spacy':
                entities = self.extract_with_spacy(normalized_text)
            elif self.model_type == 'nltk':
                entities = self.extract_with_nltk(normalized_text)
            else:  # regex fallback
                entities = self.extract_with_regex(normalized_text)
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            # Try regex fallback
            entities = self.extract_with_regex(normalized_text)
        
        # Post-process and return
        return self._post_process_entities(entities)

    def _post_process_entities(self, entities: List[Dict[str, any]]) -> List[Dict[str, str]]:
        """Lightweight post-processing of entities"""
        if not entities:
            return []
        
        # Simple deduplication
        seen = set()
        filtered_entities = []
        
        for entity in entities:
            # Create a key for deduplication
            key = (entity['text'].lower().strip(), entity['label'])
            if key not in seen and entity.get('confidence', 0) > 0.5:
                seen.add(key)
                filtered_entities.append({
                    'text': entity['text'].strip(),
                    'label': entity['label'],
                    'start': entity.get('start', 0),
                    'end': entity.get('end', 0),
                    'confidence': entity.get('confidence', 0.5)
                })
        
        return filtered_entities

    def extract_entities_by_type(self, text: str) -> Dict[str, List[str]]:
        """Extract entities grouped by type"""
        entities = self.extract_entities(text)
        grouped = defaultdict(list)
        
        for entity in entities:
            entity_text = entity['text'].strip()
            if entity_text and entity_text not in grouped[entity['label']]:
                grouped[entity['label']].append(entity_text)
        
        return dict(grouped)

    def extract_brands(self, text: str) -> List[str]:
        """Extract brands using available model"""
        entities_by_type = self.extract_entities_by_type(text)
        brands = []
        
        # Get organizations (many brands are organizations)
        organizations = entities_by_type.get('Organization', [])
        brands.extend(organizations)
        
        # Get miscellaneous entities that might be brands
        misc_entities = entities_by_type.get('Miscellaneous', [])
        for entity in misc_entities:
            if self._is_likely_brand(entity):
                brands.append(entity)
        
        # Remove duplicates
        seen = set()
        unique_brands = []
        for brand in brands:
            brand_lower = brand.lower()
            if brand_lower not in seen:
                seen.add(brand_lower)
                unique_brands.append(brand)
        
        return unique_brands

    def extract_product_mentions(self, text: str) -> List[str]:
        """Extract products using available model"""
        entities_by_type = self.extract_entities_by_type(text)
        products = []
        
        # Get explicit product entities
        product_entities = entities_by_type.get('Product', [])
        products.extend(product_entities)
        
        # Get miscellaneous entities that might be products
        misc_entities = entities_by_type.get('Miscellaneous', [])
        for entity in misc_entities:
            if self._is_likely_product(entity):
                products.append(entity)
        
        # Remove duplicates
        seen = set()
        unique_products = []
        for product in products:
            product_lower = product.lower()
            if product_lower not in seen:
                seen.add(product_lower)
                unique_products.append(product)
        
        return unique_products

    def _is_likely_brand(self, text: str) -> bool:
        """Lightweight heuristic to determine if text is likely a brand"""
        text_lower = text.lower()
        
        # Simple checks
        words = text.split()
        if len(words) > 3:
            return False
        
        # Check if it's capitalized
        if text[0].isupper() and len(text) > 2:
            return True
        
        return False

    def _is_likely_product(self, text: str) -> bool:
        """Mejorada heurística para determinar si el texto es probablemente un producto"""
        text_lower = text.lower()
        
        # Indicadores de producto ampliados
        product_indicators = [
            # Electrónica
            'phone', 'smartphone', 'laptop', 'computer', 'tablet', 'watch', 'headphones',
            'speaker', 'camera', 'tv', 'television', 'monitor', 'keyboard', 'mouse', 'charger',
            'cable', 'adapter', 'router', 'modem', 'printer', 'scanner',
            
            # Electrodomésticos
            'refrigerator', 'fridge', 'oven', 'microwave', 'blender', 'mixer', 'toaster',
            'coffee', 'maker', 'machine', 'vacuum', 'cleaner', 'washer', 'dryer',
            
            # Categorías generales
            'model', 'series', 'device', 'product', 'gadget', 'accessory', 'equipment',
            
            # Calificadores
            'pro', 'max', 'mini', 'air', 'plus', 'ultra', 'lite', 'premium', 'deluxe',
            'standard', 'basic', 'advanced', 'professional', 'home', 'portable',
            
            # Versiones
            'version', 'edition', 'generation', 'gen', 'release',
            
            # Ropa y accesorios
            'shoes', 'shirt', 'pants', 'jacket', 'coat', 'dress', 'hat', 'bag', 'backpack',
            'wallet', 'purse', 'watch', 'glasses', 'sunglasses',
            
            # Muebles
            'chair', 'table', 'desk', 'sofa', 'couch', 'bed', 'mattress', 'shelf', 'cabinet',
            
            # Automóviles
            'car', 'vehicle', 'truck', 'suv', 'sedan', 'coupe', 'convertible', 'motorcycle'
        ]
        
        # Verificar indicadores de producto
        for indicator in product_indicators:
            if indicator in text_lower:
                return True
        
        # Patrones de números de modelo
        model_patterns = [
            r'\b[A-Z]+\d+\b',                # Ej: XPS15, iPhone14
            r'\b\d+[A-Z]+\b',                # Ej: 15XL, 12Pro
            r'\b[A-Z]+[-]\d+\b',             # Ej: XPS-15, T-100
            r'\b[A-Z]+\s\d+\b',              # Ej: MacBook 13, Galaxy S22
            r'\b\d+\s?[Gg][Bb]\b',           # Ej: 64GB, 1 TB
            r'\b\d+\s?[Mm][Pp]\b',           # Ej: 48MP, 12 MP
            r'\b\d+\s?[Ii][Nn][Cc][Hh]\b',   # Ej: 55inch, 32 inch
            r'\b\d+(\.\d+)?\s?[Ii][Nn]\b',   # Ej: 5.5in, 10.1 in
            r'\b\d+[Kk]\b',                  # Ej: 4K, 8k
            r'\b\d+[Pp][Xx]\b',              # Ej: 1080px
            r'\b[Gg]en\s?\d+\b',             # Ej: Gen 5, Gen10
            r'\bv\d+(\.\d+)?\b'              # Ej: v2, v3.0
        ]
        
        for pattern in model_patterns:
            if re.search(pattern, text):
                return True
        
        # Verificar si tiene formato de producto (primera letra mayúscula, longitud razonable)
        words = text.split()
        if 1 <= len(words) <= 5 and text[0].isupper():
            # Verificar si contiene algún número (común en productos)
            if any(char.isdigit() for char in text):
                return True
        
        return False

    def extract_products_from_text(self, text: str) -> List[str]:
        """Extrae productos directamente del texto usando patrones y heurísticas"""
        products = []
        
        # Patrones comunes de productos
        product_patterns = [
            # Electrónica con números de modelo
            r'\b(?:iPhone|Galaxy|Pixel|Redmi|Xiaomi|OnePlus|iPad|MacBook|ThinkPad|Surface|Legion|Inspiron|XPS)\s?\d+(?:\s?(?:Pro|Max|Ultra|Plus|Air|Mini|Lite))?\b',
            r'\b(?:Samsung|LG|Sony|Panasonic|Vizio|TCL|Hisense)\s[A-Z0-9]+(?:-[A-Z0-9]+)?\b',
            
            # Electrodomésticos
            r'\b(?:Ninja|Instant\sPot|KitchenAid|Vitamix|Dyson|Roomba)\s[A-Z0-9]+(?:-[A-Z0-9]+)?\b',
            
            # Productos genéricos con números
            r'\b[A-Z][a-z]+\s(?:Model|Series|Version)\s[A-Z0-9]+\b',
            
            # Productos con medidas
            r'\b\d+(?:\.\d+)?\s?(?:inch|in|"|cm)\s(?:TV|Monitor|Tablet|Laptop|Screen)\b',
            r'\b\d+\s?(?:GB|TB|MP|mAh)\s[A-Z][a-zA-Z]+\b'
        ]
        
        # Buscar patrones en el texto
        for pattern in product_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                product = match.group().strip()
                if product and product not in products:
                    products.append(product)
        
        # Buscar frases que contengan "product" o "model"
        product_keywords = [
            r'(?:the|this|their|new|latest)\s+([A-Z][A-Za-z0-9]+(?:\s+[A-Za-z0-9]+){0,4})',
            r'([A-Z][A-Za-z0-9]+(?:\s+[A-Za-z0-9]+){0,4})\s+(?:product|model|device)'
        ]
        
        for pattern in product_keywords:
            matches = re.finditer(pattern, text)
            for match in matches:
                if len(match.groups()) > 0:
                    product = match.group(1).strip()
                    if product and product not in products and self._is_likely_product(product):
                        products.append(product)
        
        return products

    def extract_product_mentions(self, text: str) -> List[str]:
        """Extrae productos usando modelo disponible y patrones de texto"""
        products = []
        
        # Método 1: Usar entidades del modelo NER
        entities_by_type = self.extract_entities_by_type(text)
        
        # Obtener entidades explícitas de producto
        product_entities = entities_by_type.get('Product', [])
        products.extend(product_entities)
        
        # Obtener entidades misceláneas que podrían ser productos
        misc_entities = entities_by_type.get('Miscellaneous', [])
        for entity in misc_entities:
            if self._is_likely_product(entity):
                products.append(entity)
        
        # Método 2: Usar patrones directamente en el texto
        text_products = self.extract_products_from_text(text)
        products.extend(text_products)
        
        # Método 3: Buscar en organizaciones que podrían ser nombres de producto
        organizations = entities_by_type.get('Organization', [])
        for org in organizations:
            if self._is_likely_product(org):
                products.append(org)
        
        # Eliminar duplicados preservando orden
        seen = set()
        unique_products = []
        for product in products:
            product_lower = product.lower()
            if product_lower not in seen:
                seen.add(product_lower)
                unique_products.append(product)
        
        return unique_products

    def extract_brand_products(self, text: str) -> Dict[str, List[str]]:
        """Extrae productos asociados con marcas específicas"""
        brands = self.extract_brands(text)
        brand_products = defaultdict(list)
        
        # Para cada marca, buscar productos asociados
        for brand in brands:
            # Buscar patrones como "Brand Model X", "Brand's Product Y"
            patterns = [
                rf'\b{re.escape(brand)}\s+([A-Za-z0-9]+(?:\s+[A-Za-z0-9]+){{0,3}})',
                rf'\b{re.escape(brand)}\'s\s+([A-Za-z0-9]+(?:\s+[A-Za-z0-9]+){{0,3}})'
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    if len(match.groups()) > 0:
                        product = match.group(1).strip()
                        if product and self._is_likely_product(product):
                            brand_products[brand].append(product)
        return dict(brand_products)

    def analyze_review(self, review_text: str) -> Dict[str, any]:
        """Análisis completo de una reseña con optimización de memoria"""
        if not review_text:
            return {
                'entities': {},
                'products': [],
                'brands': [],
                'brand_products': {},
                'all_entities': []
            }
    
        try:
            # Extraer todos los tipos de entidades
            entities_by_type = self.extract_entities_by_type(review_text)
            
            # Extraer marcas y productos
            brands = self.extract_brands(review_text)
            products = self.extract_product_mentions(review_text)
            
            # Extraer productos asociados a marcas
            brand_products = self.extract_brand_products(review_text)
            
            # Obtener todas las entidades para compatibilidad
            all_entities = self.extract_entities(review_text)
            
            return {
                'entities': entities_by_type,
                'products': products,
                'brands': brands,
                'brand_products': brand_products,
                'all_entities': all_entities,
                'extraction_stats': {
                    'total_entities': len(all_entities),
                    'unique_brands': len(set(brands)),
                    'unique_products': len(set(products)),
                    'model_used': self.model_type,
                    'processed_count': self.processed_count
                }
            }
        except Exception as e:
            logger.error(f"Review analysis failed: {e}")
            return {
                'entities': {},
                'products': [],
                'brands': [],
                'brand_products': {},
                'all_entities': []
            }

    def get_extraction_statistics(self) -> Dict[str, any]:
        """Get statistics about the extraction capabilities"""
        memory_usage = self._get_memory_usage()
        
        return {
            'model_type': self.model_type,
            'processed_count': self.processed_count,
            'memory_usage_percent': memory_usage,
            'memory_optimized': True,
            'supported_entities': list(set(self.entity_mapping.values())),
            'uses_pretrained_models': self.model_type in ['spacy', 'nltk'],
            'lightweight_mode': True
        }

    def reset_memory(self):
        """Manual memory reset for batch processing"""
        self.processed_count = 0
        self._cleanup_memory()
        logger.info("Memory reset completed")

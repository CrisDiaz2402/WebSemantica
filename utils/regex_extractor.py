#1. Expresiones regulares (Encontrar menciones de precios, fechas, modelos.)
#- Archivo: `utils\regex_extractor.py`
#- Llamado en: `utils\main_processor.py` (dentro del método `process_single_review`).
#- ¿Qué Hace?: Define patrones de expresiones regulares (`self.patterns`) para identificar y extraer: 
#    ¬ precios (`extract_prices`), 
#    ¬ fechas (`extract_dates`), 
#    ¬ modelos (`extract_models`),
#    ¬ calificaciones (`extract_ratings`) 
#  del texto de las reseñas. También incluye una función `clean_text` para preprocesar el texto eliminando 
#  URLs, menciones, hashtags y normalizando espacios.

import re
import pandas as pd
from typing import List, Dict, Tuple, Optional, Set
import concurrent.futures
from functools import lru_cache
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RegexExtractor:
    """Optimized pattern extractor using regular expressions for Amazon English data"""
    
    def __init__(self):
        # Compiled regex patterns for better performance with large datasets
        self.compiled_patterns = self._compile_patterns()
        
        # Amazon-specific product model patterns
        self.amazon_product_patterns = self._compile_amazon_patterns()
        
        # Cache for frequently used operations
        self._text_cache = {}
        
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile all regex patterns for better performance"""
        patterns = {
            # Enhanced price patterns for Amazon (supports multiple currencies)
            'price': re.compile(
                r'(?:USD?|GBP|EUR|CAD)?\s*[\$£€]?\s*'
                r'(?:\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+(?:\.\d{2})?)'
                r'\s*(?:USD?|dollars?|GBP|pounds?|EUR|euros?|CAD)?',
                re.IGNORECASE
            ),
            
            # Amazon date patterns (various formats)
            'date': re.compile(
                r'(?:'
                r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b|'
                r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|'
                r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b|'
                r'\b(?:yesterday|today|last week|last month)\b'
                r')',
                re.IGNORECASE
            ),
            
            # Enhanced model patterns for Amazon products
            'model': re.compile(
                r'(?:'
                r'\b(?:iPhone|iPad|Galaxy|Pixel|MacBook|Surface|ThinkPad|XPS)\s*[A-Z0-9]+[A-Z0-9\s]*\b|'
                r'\b[A-Z]{2,}\s*[-]?\s*[0-9]+[A-Z0-9]*\b|'
                r'\bModel\s*[:#]?\s*[A-Z0-9]+[A-Z0-9\s-]*\b|'
                r'\b(?:Gen|Generation)\s*[0-9]+\b'
                r')',
                re.IGNORECASE
            ),
            
            # Amazon rating patterns (stars, scores, percentages)
            'rating': re.compile(
                r'(?:'
                r'\b[1-5](?:\.[0-9])?\s*(?:out\s*of\s*5\s*)?stars?\b|'
                r'\b[1-5]/5\b|'
                r'\b[0-9]{1,2}(?:\.[0-9])?/10\b|'
                r'\b[0-9]{1,3}%\s*(?:satisfied|recommend|positive)\b|'
                r'\b(?:excellent|good|fair|poor|terrible)\s*rating\b'
                r')',
                re.IGNORECASE
            ),
            
            # Email patterns (optimized)
            'email': re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ),
            
            # Phone patterns (US/UK/International) - FIXED
            'phone': re.compile(
                r'(?:'
                r'\+?1?[-.\s]?$$[0-9]{3}$$[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b|'
                r'\+44[-.\s]?[0-9]{4}[-.\s]?[0-9]{6}\b|'
                r'\+[0-9]{1,3}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,9}\b'
                r')'
            ),
            
            # Amazon-specific patterns
            'asin': re.compile(r'\bB[0-9A-Z]{9}\b'),  # Amazon Standard Identification Number
            'shipping': re.compile(
                r'(?:'
                r'\bfree\s+shipping\b|'
                r'\bprime\s+shipping\b|'
                r'\bdelivered\s+in\s+\d+\s+days?\b|'
                r'\bshipping\s+cost\s*[:$]\s*[\d.]+\b'
                r')',
                re.IGNORECASE
            ),
            
            # Size/dimension patterns
            'dimensions': re.compile(
                r'(?:'
                r'\b\d+(?:\.\d+)?\s*(?:x|\×)\s*\d+(?:\.\d+)?(?:\s*(?:x|\×)\s*\d+(?:\.\d+)?)?\s*(?:inches?|in|cm|mm|ft)\b|'
                r'\b\d+(?:\.\d+)?\s*(?:inches?|in|cm|mm|ft|lbs?|kg|oz|grams?)\b'
                r')',
                re.IGNORECASE
            ),
            
            # Color patterns
            'color': re.compile(
                r'\b(?:black|white|red|blue|green|yellow|orange|purple|pink|brown|gray|grey|silver|gold|rose\s+gold|space\s+gray)\b',
                re.IGNORECASE
            )
        }
        
        return patterns
    
    def _compile_amazon_patterns(self) -> Dict[str, re.Pattern]:
        """Compile Amazon-specific product patterns"""
        return {
            'electronics': re.compile(
                r'\b(?:iPhone|iPad|Samsung|Galaxy|Google|Pixel|Apple|MacBook|iMac|Dell|HP|Lenovo|ASUS|Acer|MSI|Razer|Alienware|Surface|Xbox|PlayStation|Nintendo|Switch)\b',
                re.IGNORECASE
            ),
            'home_garden': re.compile(
                r'\b(?:KitchenAid|Instant\s+Pot|Ninja|Cuisinart|Hamilton\s+Beach|Black\s*&\s*Decker|Dyson|Shark|Bissell|Roomba)\b',
                re.IGNORECASE
            ),
            'clothing': re.compile(
                r'\b(?:Nike|Adidas|Under\s+Armour|Levi\'?s|Calvin\s+Klein|Tommy\s+Hilfiger|Ralph\s+Lauren|Gap|Old\s+Navy)\b',
                re.IGNORECASE
            ),
            'books': re.compile(
                r'\b(?:Kindle|paperback|hardcover|audiobook|ISBN[-:\s]*(?:\d{10}|\d{13}))\b',
                re.IGNORECASE
            )
        }
    
    @lru_cache(maxsize=1000)
    def _cached_clean_text(self, text: str) -> str:
        """Cached version of text cleaning for frequently processed texts"""
        return self._clean_text_internal(text)
    
    def _clean_text_internal(self, text: str) -> str:
        """Internal text cleaning method"""
        # Remove URLs (optimized pattern)
        text = re.sub(r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?', '', text)
        
        # Remove mentions and hashtags
        text = re.sub(r'[@#]\w+', '', text)
        
        # Normalize spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove excessive punctuation but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-\'\"$%]', '', text)
        
        return text.strip()
    
    def extract_prices(self, text: str) -> List[Dict[str, str]]:
        """Extract price mentions with enhanced context"""
        matches = []
        try:
            for match in self.compiled_patterns['price'].finditer(text):
                price_text = match.group().strip()
                start, end = match.span()
                
                # Extract context around the price
                context_start = max(0, start - 50)
                context_end = min(len(text), end + 50)
                context = text[context_start:context_end].strip()
                
                matches.append({
                    'price': price_text,
                    'position': (start, end),
                    'context': context
                })
        except Exception as e:
            logger.error(f"Error extracting prices: {e}")
        
        return matches
    
    def extract_dates(self, text: str) -> List[Dict[str, str]]:
        """Extract dates with context"""
        matches = []
        try:
            for match in self.compiled_patterns['date'].finditer(text):
                date_text = match.group().strip()
                start, end = match.span()
                
                matches.append({
                    'date': date_text,
                    'position': (start, end),
                    'normalized': self._normalize_date(date_text)
                })
        except Exception as e:
            logger.error(f"Error extracting dates: {e}")
        
        return matches
    
    def _normalize_date(self, date_str: str) -> Optional[str]:
        """Normalize date string to standard format"""
        # Simple normalization - can be enhanced with dateutil
        date_str = date_str.lower()
        if 'yesterday' in date_str:
            return 'yesterday'
        elif 'today' in date_str:
            return 'today'
        elif 'last week' in date_str:
            return 'last_week'
        elif 'last month' in date_str:
            return 'last_month'
        return date_str
    
    def extract_models(self, text: str) -> List[Dict[str, str]]:
        """Extract product models with enhanced detection"""
        matches = []
        try:
            # Use compiled pattern
            for match in self.compiled_patterns['model'].finditer(text):
                model_text = match.group().strip()
                start, end = match.span()
                
                matches.append({
                    'model': model_text,
                    'position': (start, end),
                    'confidence': self._calculate_model_confidence(model_text)
                })
        except Exception as e:
            logger.error(f"Error extracting models: {e}")
        
        return matches
    
    def _calculate_model_confidence(self, model_text: str) -> float:
        """Calculate confidence score for model detection"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence for known patterns
        if re.search(r'\b(?:iPhone|iPad|Galaxy|Pixel|MacBook)\b', model_text, re.IGNORECASE):
            confidence += 0.3
        
        if re.search(r'\b[A-Z]{2,}\d+\b', model_text):
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def extract_ratings(self, text: str) -> List[Dict[str, str]]:
        """Extract ratings with normalization"""
        matches = []
        try:
            for match in self.compiled_patterns['rating'].finditer(text):
                rating_text = match.group().strip()
                start, end = match.span()
                
                matches.append({
                    'rating': rating_text,
                    'position': (start, end),
                    'normalized_score': self._normalize_rating(rating_text)
                })
        except Exception as e:
            logger.error(f"Error extracting ratings: {e}")
        
        return matches
    
    def _normalize_rating(self, rating_str: str) -> Optional[float]:
        """Normalize rating to 0-5 scale"""
        rating_str = rating_str.lower()
        
        # Extract numeric ratings
        if '5' in rating_str or 'excellent' in rating_str:
            return 5.0
        elif '4' in rating_str or 'good' in rating_str:
            return 4.0
        elif '3' in rating_str or 'fair' in rating_str:
            return 3.0
        elif '2' in rating_str or 'poor' in rating_str:
            return 2.0
        elif '1' in rating_str or 'terrible' in rating_str:
            return 1.0
        
        # Try to extract decimal ratings
        decimal_match = re.search(r'(\d+(?:\.\d+)?)', rating_str)
        if decimal_match:
            try:
                return float(decimal_match.group(1))
            except ValueError:
                pass
        
        return None
    
    def extract_amazon_specific(self, text: str) -> Dict[str, List[str]]:
        """Extract Amazon-specific patterns"""
        results = {}
        
        try:
            # ASIN codes
            asin_matches = [match.group() for match in self.compiled_patterns['asin'].finditer(text)]
            if asin_matches:
                results['asin'] = asin_matches
            
            # Shipping information
            shipping_matches = [match.group() for match in self.compiled_patterns['shipping'].finditer(text)]
            if shipping_matches:
                results['shipping'] = shipping_matches
            
            # Dimensions
            dimension_matches = [match.group() for match in self.compiled_patterns['dimensions'].finditer(text)]
            if dimension_matches:
                results['dimensions'] = dimension_matches
            
            # Colors
            color_matches = [match.group() for match in self.compiled_patterns['color'].finditer(text)]
            if color_matches:
                results['colors'] = color_matches
            
            # Product categories
            for category, pattern in self.amazon_product_patterns.items():
                category_matches = [match.group() for match in pattern.finditer(text)]
                if category_matches:
                    results[f'{category}_brands'] = category_matches
        
        except Exception as e:
            logger.error(f"Error extracting Amazon-specific patterns: {e}")
        
        return results
    
    def extract_all_patterns(self, text: str) -> Dict[str, any]:
        """Extract all patterns from text with enhanced performance"""
        try:
            # Extract all patterns first
            prices = self.extract_prices(text)
            dates = self.extract_dates(text)
            models = self.extract_models(text)
            ratings = self.extract_ratings(text)
            amazon_specific = self.extract_amazon_specific(text)
            
            # Calculate total patterns found
            total_patterns = (
                len(prices) + 
                len(dates) + 
                len(models) + 
                len(ratings) + 
                sum(len(v) if isinstance(v, list) else 0 for v in amazon_specific.values())
            )
            
            # Build results dictionary
            results = {
                'prices': prices,
                'dates': dates,
                'models': models,
                'ratings': ratings,
                'amazon_specific': amazon_specific,
                'summary': {
                    'total_patterns_found': total_patterns,
                    'text_length': len(text),
                    'processing_successful': True
                }
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error extracting patterns: {e}")
            return {
                'prices': [],
                'dates': [],
                'models': [],
                'ratings': [],
                'amazon_specific': {},
                'summary': {
                    'total_patterns_found': 0,
                    'text_length': len(text) if text else 0,
                    'processing_successful': False,
                    'error': str(e)
                }
            }
    
    def clean_text(self, text: str) -> str:
        """Clean text using cached method for better performance"""
        if not text or not isinstance(text, str):
            return ""
        
        try:
            # Use cached version for frequently processed texts
            if len(text) < 1000:  # Cache smaller texts
                return self._cached_clean_text(text)
            else:
                return self._clean_text_internal(text)
        except Exception as e:
            logger.error(f"Error cleaning text: {e}")
            return text  # Return original text if cleaning fails
    
    def batch_extract(self, texts: List[str], max_workers: int = 4) -> List[Dict[str, any]]:
        """Process multiple texts in parallel for large datasets"""
        if not texts:
            return []
        
        logger.info(f"Processing {len(texts)} texts with {max_workers} workers")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_text = {
                executor.submit(self.extract_all_patterns, text): i 
                for i, text in enumerate(texts)
            }
            
            results = [None] * len(texts)
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_text):
                text_index = future_to_text[future]
                try:
                    result = future.result()
                    results[text_index] = result
                except Exception as e:
                    logger.error(f"Error processing text {text_index}: {e}")
                    results[text_index] = {
                        'prices': [],
                        'dates': [],
                        'models': [],
                        'ratings': [],
                        'amazon_specific': {},
                        'summary': {
                            'total_patterns_found': 0,
                            'text_length': len(texts[text_index]) if text_index < len(texts) else 0,
                            'processing_successful': False,
                            'error': str(e)
                        }
                    }
        
        logger.info(f"Completed processing {len(texts)} texts")
        return results
    
    def get_statistics(self) -> Dict[str, any]:
        """Get performance statistics"""
        return {
            'compiled_patterns': len(self.compiled_patterns),
            'amazon_patterns': len(self.amazon_product_patterns),
            'cache_size': len(self._text_cache),
            'supported_features': [
                'prices', 'dates', 'models', 'ratings', 'asin', 
                'shipping', 'dimensions', 'colors', 'product_categories'
            ]
        }
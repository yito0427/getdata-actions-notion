"""
Notion API Rate Limiter for optimal performance
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from loguru import logger


class NotionRateLimiter:
    """
    Notion API Rate Limiter
    
    Implements Notion's rate limits:
    - 3 requests per second average
    - 2,700 requests per 15-minute window
    """
    
    def __init__(self, requests_per_second: float = 0.5, window_minutes: int = 15):
        """
        Initialize rate limiter
        
        Args:
            requests_per_second: Target RPS (0.5 recommended for reliability)
            window_minutes: Rate limit window (15 for Notion)
        """
        self.rps = requests_per_second
        self.window_seconds = window_minutes * 60
        self.max_requests_per_window = int(2700 * 0.8)  # 80% of Notion's limit for safety
        
        # Track requests in current window
        self.request_times = []
        self.last_request_time = 0
        
        # Semaphore for concurrent request limiting
        self.semaphore = asyncio.Semaphore(1)  # Only 1 concurrent request
        
    async def acquire(self) -> None:
        """Acquire permission to make a request"""
        async with self.semaphore:
            await self._wait_for_rate_limit()
            self._cleanup_old_requests()
            
            # Check window limit
            if len(self.request_times) >= self.max_requests_per_window:
                wait_time = self.window_seconds - (time.time() - self.request_times[0])
                if wait_time > 0:
                    logger.warning(f"Notion rate limit window exceeded. Waiting {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)
                    self._cleanup_old_requests()
            
            # Record this request
            now = time.time()
            self.request_times.append(now)
            self.last_request_time = now
            
            logger.debug(f"Rate limiter: {len(self.request_times)} requests in current window")
    
    async def _wait_for_rate_limit(self) -> None:
        """Wait to maintain target RPS"""
        if self.last_request_time > 0:
            elapsed = time.time() - self.last_request_time
            min_interval = 1.0 / self.rps
            
            if elapsed < min_interval:
                wait_time = min_interval - elapsed
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
    
    def _cleanup_old_requests(self) -> None:
        """Remove requests outside the current window"""
        cutoff_time = time.time() - self.window_seconds
        self.request_times = [t for t in self.request_times if t > cutoff_time]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current rate limiter statistics"""
        self._cleanup_old_requests()
        
        return {
            "requests_in_window": len(self.request_times),
            "window_limit": self.max_requests_per_window,
            "utilization_percent": (len(self.request_times) / self.max_requests_per_window) * 100,
            "target_rps": self.rps,
            "window_minutes": self.window_seconds / 60
        }


class NotionBatchProcessor:
    """
    Processes data in batches optimized for Notion API
    """
    
    def __init__(self, rate_limiter: NotionRateLimiter, batch_size: int = 10):
        """
        Initialize batch processor
        
        Args:
            rate_limiter: Rate limiter instance
            batch_size: Number of exchanges to process per batch
        """
        self.rate_limiter = rate_limiter
        self.batch_size = batch_size
        
    async def process_exchange_data(self, exchange_data_list: list, processor_func) -> list:
        """
        Process multiple exchanges with rate limiting
        
        Args:
            exchange_data_list: List of exchange data to process
            processor_func: Async function to process each exchange
            
        Returns:
            List of processing results
        """
        results = []
        
        # Process in batches
        for i in range(0, len(exchange_data_list), self.batch_size):
            batch = exchange_data_list[i:i + self.batch_size]
            
            logger.info(f"Processing batch {i//self.batch_size + 1}: {len(batch)} exchanges")
            
            # Process each item in batch with rate limiting
            batch_results = []
            for exchange_data in batch:
                await self.rate_limiter.acquire()
                
                try:
                    result = await processor_func(exchange_data)
                    batch_results.append(result)
                    
                except Exception as e:
                    logger.error(f"Failed to process {exchange_data.get('exchange', 'unknown')}: {e}")
                    batch_results.append({"error": str(e)})
            
            results.extend(batch_results)
            
            # Optional: Inter-batch delay for additional safety
            if i + self.batch_size < len(exchange_data_list):
                await asyncio.sleep(1)
                
        return results


class NotionOptimizedUploader:
    """
    Optimized uploader with rate limiting and batch processing
    """
    
    def __init__(self, notion_client, target_rps: float = 0.5):
        """
        Initialize optimized uploader
        
        Args:
            notion_client: Notion API client
            target_rps: Target requests per second
        """
        self.client = notion_client
        self.rate_limiter = NotionRateLimiter(target_rps)
        self.batch_processor = NotionBatchProcessor(self.rate_limiter)
        
        # Performance tracking
        self.total_requests = 0
        self.total_errors = 0
        self.start_time = None
        
    async def upload_crypto_data(self, crypto_data_list: list) -> Dict[str, Any]:
        """
        Upload crypto data with optimization
        
        Args:
            crypto_data_list: List of crypto data to upload
            
        Returns:
            Upload summary
        """
        self.start_time = datetime.now()
        
        logger.info(f"Starting optimized upload of {len(crypto_data_list)} exchanges")
        
        # Process data in batches
        results = await self.batch_processor.process_exchange_data(
            crypto_data_list,
            self._upload_single_exchange
        )
        
        # Generate summary
        return self._generate_summary(results)
    
    async def _upload_single_exchange(self, exchange_data) -> Dict[str, Any]:
        """Upload data for a single exchange"""
        try:
            self.total_requests += 1
            
            # Your existing upload logic here
            result = await self._do_notion_upload(exchange_data)
            
            logger.info(f"✅ Uploaded {exchange_data.get('exchange', 'unknown')}")
            return {
                "exchange": exchange_data.get('exchange'),
                "status": "success",
                "records": result.get('records', 0)
            }
            
        except Exception as e:
            self.total_errors += 1
            logger.error(f"❌ Failed {exchange_data.get('exchange', 'unknown')}: {e}")
            return {
                "exchange": exchange_data.get('exchange'),
                "status": "error",
                "error": str(e)
            }
    
    async def _do_notion_upload(self, exchange_data) -> Dict[str, Any]:
        """Upload data using SimpleNotionUploader with rate limiting"""
        from .simple_uploader import SimpleNotionUploader
        
        # Create uploader instance
        uploader = SimpleNotionUploader()
        
        # Extract the CollectedData from exchange_data
        data = exchange_data.get("data")
        if not data:
            raise ValueError("No data found in exchange_data")
            
        # Upload the data
        result = await uploader.upload_exchange_data(data)
        
        return {
            "records": result.get("records_uploaded", 0),
            "status": result.get("status", "unknown")
        }
    
    def _generate_summary(self, results: list) -> Dict[str, Any]:
        """Generate upload summary"""
        successful = sum(1 for r in results if r.get('status') == 'success')
        failed = sum(1 for r in results if r.get('status') == 'error')
        
        duration = datetime.now() - self.start_time if self.start_time else timedelta(0)
        
        # Get rate limiter stats
        rate_stats = self.rate_limiter.get_stats()
        
        return {
            "summary": {
                "total_exchanges": len(results),
                "successful": successful,
                "failed": failed,
                "success_rate": f"{(successful/len(results)*100):.1f}%" if results else "0%",
                "duration_seconds": duration.total_seconds(),
                "total_requests": self.total_requests,
                "total_errors": self.total_errors
            },
            "rate_limiting": rate_stats,
            "results": results
        }
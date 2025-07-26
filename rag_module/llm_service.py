import os
from typing import List, Dict, Any, Tuple
from openai import OpenAI


class LLMService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "1000"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))

    async def generate_answer(
        self, 
        question: str, 
        context_chunks: List[Dict[str, Any]]
    ) -> Tuple[str, int, int, float]:
        context = "\n\n".join([
            f"Document {chunk['document_id']} (chunk {chunk['chunk_index']}):\n{chunk['text']}"
            for chunk in context_chunks
        ])

        system_prompt = """You are a helpful assistant that answers questions based on the provided context. 
        Use only the information from the context to answer questions. If the context doesn't contain 
        enough information to answer the question, say so clearly."""

        user_prompt = f"""Context:
{context}

Question: {question}

Please provide a comprehensive answer based on the context above."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            answer = response.choices[0].message.content
            tokens_consumed = response.usage.prompt_tokens
            tokens_generated = response.usage.completion_tokens
            
            confidence_score = self._calculate_confidence(answer, context_chunks)

            return answer, tokens_consumed, tokens_generated, confidence_score

        except Exception as e:
            raise ValueError(f"Failed to generate answer: {str(e)}")

    def _calculate_confidence(self, answer: str, context_chunks: List[Dict[str, Any]]) -> float:
        if not answer or "don't have enough information" in answer.lower():
            return 0.3
        
        if len(context_chunks) == 0:
            return 0.2
        
        avg_score = sum(chunk.get('score', 0.5) for chunk in context_chunks) / len(context_chunks)
        
        answer_length_factor = min(len(answer) / 100, 1.0)
        
        confidence = (avg_score * 0.7) + (answer_length_factor * 0.3)
        
        return min(max(confidence, 0.1), 0.95)
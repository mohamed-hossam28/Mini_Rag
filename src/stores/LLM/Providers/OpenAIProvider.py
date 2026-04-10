from ..LLMInterface import LLMInterface
from openai import OpenAI
import logging
from ..LLMEnums import OpenAIEnums

class OpenAIProvider(LLMInterface):
    def __init__(self,api_key:str,api_url:str=None,default_input_max_characters:int=1000,
                default_generation_max_output_tokens:int=1000,default_generation_temperature:float=0.1):


        self.api_key = api_key
        self.api_url = api_url
        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_output_tokens = default_generation_max_output_tokens
        self.default_generation_temperature = default_generation_temperature

        self.generation_model_id = None

        self.embedding_model_id = None
        self.embedding_size = None
        self.enums = OpenAIEnums

        self.client=OpenAI(
            api_key=api_key,
            base_url=api_url
        )

        self.logger = logging.getLogger(__name__)  

    #set generation_model to eassily change the model in runtime
    def set_generation_model(self,model_id:str): 
        self.generation_model_id=model_id

    #set embedding_model to eassily change the model in runtime
    def set_embedding_model(self,model_id:str,embedding_size:int):
        self.embedding_model_id=model_id
        self.embedding_size=embedding_size

    #process text to limit the length of the text        
    def process_text(self,text:str):
        return text[:self.default_input_max_characters].strip()
        
    #construct prompt in openai format to be sent to the model
    def construct_prompt(self,prompt:str,role:str):
        return {
            "role":role,
            "content":prompt
        }

    #generate text using the generation model
    def generate_text(self,prompt:str,chat_history=[],max_output_tokens:int=None,temperature:float=None):
        
        if not self.client:
            self.logger.error("OpenAI client was not set")
            return None

        if not self.generation_model_id :
            self.logger.error("OpenAI generation model was not set")
            return None

        max_output_tokens=max_output_tokens if max_output_tokens else self.default_generation_max_output_tokens
        temperature=temperature if temperature else self.default_generation_temperature

        chat_history.append(
            self.construct_prompt(prompt,OpenAIEnums.USER.value)
        )

        try:
            response=self.client.chat.completions.create(
                model=self.generation_model_id,
                messages=chat_history,
                max_tokens=max_output_tokens,
                temperature=temperature
            )
        except Exception as e:
            self.logger.error(f"Exception while generating text with OpenAI: {e}")
            return None

        if not response or not response.choices or len(response.choices)==0 or not response.choices[0].message:
            self.logger.error("Error while generating text with OpenAI: Invalid response structure")
            return None

        choice = response.choices[0]
        if choice.finish_reason == "length":
            self.logger.warning("OpenAI generation truncated due to max_token limit. Consider increasing GENERATION_DAFAULT_MAX_TOKENS.")
        
        content = choice.message.content
        
        if not content:
            # Check if there is reasoning content (for reasoning models)
            if hasattr(choice.message, 'reasoning') and choice.message.reasoning:
                self.logger.warning("OpenAI returned reasoning but no content. The model likely ran out of tokens while reasoning.")
                return None # Or return choice.message.reasoning if appropriate, but usually we want the final answer.
            
            self.logger.error("Error while generating text with OpenAI: Empty content in response")
            self.logger.error(f"Full Response: {response}")
            return None

        return content


    def embed_text(self,text:str,document_type:str):
        if not self.client:
            self.logger.error("OpenAI client was not set")
            return None

        if not self.embedding_model_id :
            self.logger.error("OpenAI embedding model was not set")
            return None

        response=self.client.embeddings.create(
            model=self.embedding_model_id,
            input=text
        )
        if not response or not response.data or len(response.data) == 0 or not response.data[0].embedding:
            self.logger.error("Error while embedding text with OpenAI")
            return None

        return response.data[0].embedding   


















from base.config import config
from sentence_transformers import CrossEncoder

model1 = CrossEncoder(model_name=config.MODELS_DIR + "/bge-reranker-large")
# [[问题, 回答]]
pairs = [
            ['what is panda?', 'hi'],
            ['what is panda?', 'The giant panda '],
            ['what is panda?', "what is panda?"],
         ]

print(model1.predict(pairs))  # [0.00365302    0.33621186    0.999556  ]

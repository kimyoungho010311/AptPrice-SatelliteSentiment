import ee

# GEE 초기화 (이미 인증한 경우)
ee.Authenticate()  # 브라우저가 열리며 인증 요청됨
ee.Initialize()  # 또는 ee.Initialize()만 사용



# 관심 지점: 서울
seoul = ee.Geometry.Point([126.9780, 37.5665])

# Landsat 8 Collection 2, Level-2 Surface Reflectance 데이터 불러오기
image = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
         .filterBounds(seoul) \
         .filterDate('2020-01-01', '2020-12-31') \
         .sort('CLOUD_COVER') \
         .first()

# NDVI 계산: (SR_B5 - SR_B4) / (SR_B5 + SR_B4)
ndvi = image.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')

# 서울 반경 1km에서 평균 NDVI 계산
mean_ndvi = ndvi.reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=seoul.buffer(1000),
    scale=30
)

# 결과 출력
print(mean_ndvi.getInfo())
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from monitoring.models import Lote
from hardware.models import ConfiguracionSistema
from .models import Clasificacion

class ClassificationTestCase(APITestCase):
    def setUp(self):
        # Crear Lote de prueba
        self.lote = Lote.objects.create(
            codigo="LOTE-TEST-004",
            nombre="Lote de Capturas"
        )
        # Crear una Configuración del Sistema con umbral del 80%
        self.config = ConfiguracionSistema.objects.create(
            umbral_confianza=0.80,
            modo_simulado=True
        )
        
        # Crear una imagen JPEG simulada
        self.dummy_image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\x08\x06\x06'
        self.upload_url = reverse('api-classification-capture')

    def test_upload_valid_image(self):
        image = SimpleUploadedFile("mango.jpg", self.dummy_image_data, content_type="image/jpeg")
        response = self.client.post(
            self.upload_url,
            {'imagen': image, 'lot_code': self.lote.codigo},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('clase_predicha', response.data)
        self.assertIn('confianza', response.data)
        
        # Verificar que se guardó en la base de datos
        clasificacion = Clasificacion.objects.get(lote=self.lote, secuencia=1)
        self.assertEqual(clasificacion.secuencia, 1)
        self.assertIsNotNone(clasificacion.imagen_original)
        self.assertTrue(clasificacion.imagen_original.name.startswith("classifications/LOTE-TEST-004_"))


    def test_upload_invalid_extension(self):
        text_file = SimpleUploadedFile("mango.txt", b"dummy content", content_type="text/plain")
        response = self.client.post(
            self.upload_url,
            {'imagen': text_file, 'lot_code': self.lote.codigo},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Formato de imagen no permitido. Use JPEG, PNG o WebP.')

    def test_upload_missing_params(self):
        response = self.client.post(
            self.upload_url,
            {'lot_code': self.lote.codigo},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'La imagen es requerida.')

    def test_upload_non_existent_lot(self):
        image = SimpleUploadedFile("mango.jpg", self.dummy_image_data, content_type="image/jpeg")
        response = self.client.post(
            self.upload_url,
            {'imagen': image, 'lot_code': 'LOT-NOT-FOUND'},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_sequence_increment(self):
        # Subir primera imagen
        image1 = SimpleUploadedFile("mango1.jpg", self.dummy_image_data, content_type="image/jpeg")
        self.client.post(self.upload_url, {'imagen': image1, 'lot_code': self.lote.codigo}, format='multipart')
        
        # Subir segunda imagen
        image2 = SimpleUploadedFile("mango2.jpg", self.dummy_image_data, content_type="image/jpeg")
        response = self.client.post(self.upload_url, {'imagen': image2, 'lot_code': self.lote.codigo}, format='multipart')
        
        self.assertEqual(response.data['secuencia'], 2)
        self.assertEqual(Clasificacion.objects.filter(lote=self.lote).count(), 2)

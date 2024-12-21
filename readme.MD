# IPBU - Hoja de Costos en Odoo

## Descripción

El **IPBU** (Hoja de Costos) es un documento utilizado en el proceso de cotización, que se genera antes de emitir la cotización final. Este documento contiene información detallada sobre los costos de los productos y servicios que serán cotizados al cliente. En otras palabras, es una etapa preliminar en el flujo de ventas que permite analizar los costos antes de formalizar una cotización. 

En este módulo de Odoo, hemos implementado un modelo para generar y gestionar las hojas de costos (IPBU), que están asociadas a oportunidades de negocio y se gestionan antes de la creación de una cotización formal.

## Características

- **Generación automática del código de IPBU**: Cada documento IPBU se genera con un código único basado en un prefijo y un número secuencial.
- **Relación con Oportunidades de Venta**: Los documentos IPBU pueden asociarse con oportunidades de negocio en Odoo.
- **Accesos**: Permite controlar el acceso a los modelos de IPBU y sus productos.

## Instalación

### Requisitos Previos

1. Tener una instalación de **Odoo Enterprise** en **Odoo.sh**.
2. Tener permisos de administrador en Odoo.sh para instalar módulos personalizados.
3. Asegurarse de que el módulo `ipbu` se encuentra disponible en tu repositorio de Git (o en un archivo comprimido .zip) para ser subido a Odoo.sh.

### Pasos para la Instalación

#### 1. Subir el Módulo a Odoo.sh

- Si el módulo `ipbu` está en un repositorio Git, simplemente asegúrate de tener acceso a ese repositorio desde Odoo.sh.
- Si el módulo está en un archivo comprimido `.zip`, sigue estos pasos:
  1. Ve a la interfaz de Odoo.sh.
  2. En la barra superior, selecciona tu base de datos y el proyecto donde deseas instalar el módulo.
  3. Haz clic en el menú de **Aplicaciones** y selecciona **Subir módulo**.
  4. Carga el archivo `.zip` del módulo `ipbu`.

#### 2. Instalar el Módulo

1. Después de haber subido el módulo, regresa al menú de **Aplicaciones** en Odoo.
2. Busca "IPBU" en el buscador de módulos.
3. Haz clic en **Instalar** para instalar el módulo en tu instancia de Odoo.

#### 3. Configuración del Secuencial de Código IPBU

Una vez instalado el módulo, es importante configurar la secuencia para los códigos de los documentos IPBU. Esto se realiza automáticamente al instalar el módulo, pero en caso de necesitar una configuración manual, sigue estos pasos:

1. Entra en el menú **Configuración** de Odoo.
2. Busca **Secuencias** en la barra de búsqueda.
3. Localiza la secuencia `ipbu.code`, que se utiliza para generar los códigos únicos de los documentos IPBU.
4. Si es necesario, puedes configurar los valores de esta secuencia, como el prefijo, el número de incremento y el número siguiente.

#### 4. Acceso y Permisos

Asegúrate de que los usuarios que necesiten gestionar los documentos IPBU tengan los permisos adecuados. Puedes ajustar los permisos de acceso a los modelos de IPBU y productos asociados desde la configuración de seguridad y usuarios de Odoo.

## Estructura del Módulo

El módulo contiene los siguientes componentes principales:

1. **Modelo `ipbu.ipbu`**: Este modelo define los documentos IPBU y sus detalles.
2. **Modelo `ipbu.product.line`**: Define las líneas de productos asociadas a un IPBU.
3. **Secuencia `ipbu.code`**: Se utiliza para generar un código único para cada documento IPBU.
4. **Vista de acción de ventana**: Permite ver los documentos IPBU asociados a una oportunidad.
5. **Reglas de acceso**: Controla el acceso a los modelos IPBU y sus productos.

## Contribuciones

Si deseas contribuir con mejoras o nuevas funcionalidades al módulo, por favor abre un **pull request** en el repositorio o contacta con el administrador del sistema.

## Contacto

Para más información, dudas o asistencia, contacta con el administrador de tu sistema Odoo o con el desarrollador del módulo.

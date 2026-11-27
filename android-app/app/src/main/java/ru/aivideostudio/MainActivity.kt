package ru.aivideostudio

import android.app.DownloadManager
import android.content.Context
import android.graphics.Color
import android.net.Uri
import android.os.Bundle
import android.os.Environment
import android.view.Gravity
import android.view.View
import android.widget.*
import android.app.Activity
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.nio.charset.StandardCharsets

class MainActivity : Activity() {
    private lateinit var apiKey: EditText
    private lateinit var topic: EditText
    private lateinit var duration: Spinner
    private lateinit var ratio: Spinner
    private lateinit var status: TextView
    private lateinit var generate: Button
    private val model = "fal-ai/kling-video/v3/standard/text-to-video"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = Color.rgb(10, 14, 28)
        window.navigationBarColor = Color.rgb(10, 14, 28)
        buildScreen()
    }

    private fun buildScreen() {
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(22), dp(28), dp(22), dp(24))
            setBackgroundColor(Color.rgb(10, 14, 28))
        }
        val scroll = ScrollView(this)
        val content = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        scroll.addView(content)
        content.addView(label("AI VIDEO STUDIO", 27, Color.WHITE, true))
        content.addView(label("Автоматическая генерация видео по теме", 15, Color.rgb(170, 184, 211)))
        content.addView(space(22))
        content.addView(label("ТЕМА ИЛИ СЮЖЕТ", 12, Color.rgb(130, 170, 255), true))
        topic = EditText(this).apply {
            hint = "Например: детективная история в заброшенном городе"
            setTextColor(Color.WHITE); setHintTextColor(Color.rgb(120, 132, 155))
            textSize = 16f; minLines = 4; gravity = Gravity.TOP
            setPadding(dp(14), dp(14), dp(14), dp(14))
            setBackgroundColor(Color.rgb(25, 33, 54))
        }
        content.addView(topic, matchWrap())
        content.addView(space(18))
        content.addView(label("ДЛИТЕЛЬНОСТЬ", 12, Color.rgb(130, 170, 255), true))
        duration = spinner(listOf("5 секунд", "10 секунд", "15 секунд"))
        content.addView(duration, matchWrap())
        content.addView(space(14))
        content.addView(label("ФОРМАТ", 12, Color.rgb(130, 170, 255), true))
        ratio = spinner(listOf("Вертикальный 9:16 (Shorts)", "Горизонтальный 16:9", "Квадрат 1:1"))
        content.addView(ratio, matchWrap())
        content.addView(space(18))
        content.addView(label("КЛЮЧ FAL.AI", 12, Color.rgb(130, 170, 255), true))
        apiKey = EditText(this).apply {
            hint = "Вставь API-ключ fal.ai"
            setTextColor(Color.WHITE); setHintTextColor(Color.rgb(120, 132, 155))
            textSize = 15f; inputType = 129
            setPadding(dp(14), dp(13), dp(14), dp(13))
            setBackgroundColor(Color.rgb(25, 33, 54))
        }
        content.addView(apiKey, matchWrap())
        content.addView(label("Ключ используется только на этом устройстве и не отправляется в GitHub. Не вставляй его в публичные чаты.", 12, Color.rgb(150, 160, 181)))
        content.addView(space(22))
        generate = Button(this).apply {
            text = "СОЗДАТЬ ВИДЕО"; textSize = 15f; isAllCaps = false
            setTextColor(Color.WHITE)
            setBackgroundTintList(android.content.res.ColorStateList.valueOf(Color.rgb(72, 105, 235)))
            setOnClickListener { startGeneration() }
        }
        content.addView(generate, matchWrap())
        content.addView(space(14))
        status = label("Готово к работе. Для генерации нужен ключ fal.ai; сама генерация оплачивается по тарифам провайдера.", 14, Color.rgb(188, 198, 218))
        content.addView(status)
        content.addView(space(18))
        content.addView(label("Движок: Kling Video 3 Standard через fal.ai. Генерация происходит в облаке; приложение сохраняет готовый MP4 в папку Movies.", 12, Color.rgb(115, 129, 154)))
        root.addView(scroll, LinearLayout.LayoutParams(-1, 0, 1f))
        setContentView(root)
    }

    private fun startGeneration() {
        val key = apiKey.text.toString().trim()
        val rawTopic = topic.text.toString().trim()
        if (key.isEmpty()) { apiKey.error = "Нужен API-ключ fal.ai"; return }
        if (rawTopic.length < 5) { topic.error = "Опиши тему подробнее"; return }
        val seconds = listOf("5", "10", "15")[duration.selectedItemPosition]
        val aspect = listOf("9:16", "16:9", "1:1")[ratio.selectedItemPosition]
        generate.isEnabled = false
        status.text = "Отправляю запрос на генерацию…"
        Thread {
            try {
                val cinematicPrompt = "Create a cinematic, photorealistic live-action video based on this idea: $rawTopic. " +
                    "Real human actors, natural facial expressions, believable body movement, coherent scene, " +
                    "professional camera movement, realistic lighting, detailed environment, film color grading. " +
                    "No illustration, no slideshow, no static image, no cartoon."
                val payload = JSONObject()
                    .put("prompt", cinematicPrompt)
                    .put("duration", seconds)
                    .put("aspect_ratio", aspect)
                    .put("generate_audio", false)
                    .put("shot_type", "intelligent")
                    .put("negative_prompt", "cartoon, illustration, slideshow, still image, distorted face, extra fingers, blurry, low quality")
                val submit = request("https://queue.fal.run/$model", "POST", key, payload.toString())
                val requestId = submit.optString("request_id")
                if (requestId.isBlank()) throw IllegalStateException("Сервис не вернул request_id: $submit")
                updateStatus("Задание принято. Ожидаю завершения генерации…")
                var completed = false
                for (attempt in 1..90) {
                    Thread.sleep(5000)
                    val state = request("https://queue.fal.run/$model/requests/$requestId/status", "GET", key)
                    val phase = state.optString("status")
                    updateStatus("Генерация: $phase ($attempt/90)")
                    if (phase == "COMPLETED") { completed = true; break }
                    if (phase == "FAILED" || phase == "ERROR") throw IllegalStateException("Генерация завершилась ошибкой: $state")
                }
                if (!completed) throw IllegalStateException("Сервис не завершил задачу за отведённое время. Проверь историю запросов fal.ai.")
                val result = request("https://queue.fal.run/$model/requests/$requestId", "GET", key)
                val videoUrl = result.optJSONObject("video")?.optString("url").orEmpty()
                if (!videoUrl.startsWith("https://")) throw IllegalStateException("В ответе нет ссылки на MP4: $result")
                val dm = getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
                val req = DownloadManager.Request(Uri.parse(videoUrl))
                    .setTitle("AI Video Studio — готовое видео")
                    .setDescription("Сохранение готового ролика")
                    .setMimeType("video/mp4")
                    .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
                    .setDestinationInExternalPublicDir(Environment.DIRECTORY_MOVIES, "AI_Video_${System.currentTimeMillis()}.mp4")
                dm.enqueue(req)
                updateStatus("Готово. MP4 сохраняется в Movies. Уведомление появится после загрузки файла.")
            } catch (e: Exception) {
                updateStatus("Ошибка: ${e.message ?: "неизвестная ошибка"}")
            } finally {
                runOnUiThread { generate.isEnabled = true }
            }
        }.start()
    }

    private fun request(url: String, method: String, key: String, body: String? = null): JSONObject {
        val connection = URL(url).openConnection() as HttpURLConnection
        try {
            connection.requestMethod = method
            connection.connectTimeout = 30000
            connection.readTimeout = 60000
            connection.setRequestProperty("Authorization", "Key $key")
            connection.setRequestProperty("Accept", "application/json")
            if (body != null) {
                connection.doOutput = true
                connection.setRequestProperty("Content-Type", "application/json")
                connection.outputStream.use { it.write(body.toByteArray(StandardCharsets.UTF_8)) }
            }
            val code = connection.responseCode
            val stream = if (code in 200..299) connection.inputStream else connection.errorStream
            val text = stream?.bufferedReader(StandardCharsets.UTF_8)?.use { it.readText() }.orEmpty()
            if (code !in 200..299) throw IllegalStateException("HTTP $code: $text")
            return JSONObject(text)
        } finally { connection.disconnect() }
    }

    private fun updateStatus(message: String) = runOnUiThread { status.text = message }
    private fun spinner(items: List<String>) = Spinner(this).apply {
        adapter = ArrayAdapter(this@MainActivity, android.R.layout.simple_spinner_dropdown_item, items)
        setPadding(dp(8), dp(4), dp(8), dp(4))
    }
    private fun label(text: String, size: Int, color: Int, bold: Boolean = false) =
        TextView(this).apply {
            this.text = text; textSize = size.toFloat(); setTextColor(color)
            if (bold) setTypeface(null, android.graphics.Typeface.BOLD)
            setPadding(0, dp(5), 0, dp(5))
        }
    private fun space(height: Int) = View(this).apply { layoutParams = LinearLayout.LayoutParams(1, dp(height)) }
    private fun matchWrap() = LinearLayout.LayoutParams(-1, -2).apply { bottomMargin = dp(4) }
    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()
}

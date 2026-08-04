#include <WiFi.h>
#include <WiFiManager.h>
#include <WebServer.h>
#include <Arduino.h>
#include <IRremoteESP8266.h>
#include <IRsend.h>
#include <vector>



// ========== 文件开头，自定义路径名，修改这里即可 ==========
const String controllerPath = "/local_mcp/controller__toilet";
const String apName = "local_mcp.controller__toilet";
// ========================================================


// ======================== 【1. 基础单条红外指令】 ========================
struct RawCommand {const char* cmdName; std::vector<uint16_t> rawData;};
const std::vector<RawCommand> rawCmdList = {
{"步骤1",{3550,  1740,  486,  418,  464,  1300,  436,  444,  436,  444,  438,  416,  462,  440,  440,  416,  464,  416,  462,  420,  462,  418,  464,  418,  460,  418,  464,  416,  464,  1322,  440,  442,  436,  418,  466,  416,  462,  416,  464,  418,  460,  416,  464,  416,  462,  416,  462,  416,  462,  416,  462,  416,  462,  418,  460,  420,  462,  1300,  460,  418,  464,  416,  464,  418,  486,  392,  462,  420,  462,  416,  464,  416,  464,  416,  460,  1300,  458,  1300,  460,  1300,  460,  1300,  462,  1298,  460,  420,  454,  426,  452,  428,  452,  428,  456,  424,  452,  1306,  456,  424,  452,  428,  452,  1308,  452,  1310,  454,  1306,  454,  1306,  452,  1308,  454,  426,  452,  1310,  456,  1306,  456,  426,  452,  428,  452,  428,  452,  426,  452,  428,  452,  426,  452,  428,  452,  428,  452,  1308,  458,  420,  452,  428,  452,  428,  452,  428,  452,  426,  452,  432,  452}},
{"步骤2",{3550,  1740,  488,  416,  436,  1300,  486,  394,  462,  416,  462,  418,  486,  416,  462,  394,  486,  390,  488,  418,  434,  422,  484,  394,  462,  420,  458,  420,  462,  1300,  464,  418,  466,  418,  462,  444,  438,  418,  464,  414,  464,  416,  464,  414,  464,  418,  460,  420,  458,  418,  464,  416,  464,  418,  464,  418,  462,  1298,  464,  416,  464,  416,  462,  420,  462,  418,  460,  418,  460,  420,  456,  424,  460,  420,  456,  1304,  430,  1332,  458,  1304,  458,  1304,  458,  1304,  454,  1310,  456,  424,  452,  428,  452,  428,  452,  428,  452,  430,  454,  1308,  452,  428,  452,  428,  454,  1308,  458,  1302,  452,  1306,  452,  1308,  452,  1308,  458,  420,  452,  1308,  456,  424,  452,  428,  452,  428,  452,  1308,  458,  1306,  458,  422,  454,  428,  452,  428,  452,  1308,  482,  396,  452,  428,  452,  428,  452,  428,  452,  426,  452,  432,  452}},
{"关闭",{3550,  1738,  460,  440,  438,  1302,  464,  420,  460,  418,  460,  418,  462,  416,  464,  416,  462,  416,  460,  420,  460,  422,  456,  422,  436,  444,  456,  422,  454,  1310,  454,  426,  452,  428,  452,  426,  452,  428,  452,  426,  452,  426,  452,  426,  452,  428,  452,  428,  452,  428,  452,  428,  452,  428,  452,  426,  452,  1310,  482,  398,  452,  430,  452,  430,  452,  426,  452,  428,  452,  428,  452,  430,  452,  428,  452,  1308,  484,  1276,  482,  1282,  480,  1280,  482,  396,  482,  396,  484,  1278,  486,  1276,  466,  414,  482,  396,  460,  422,  458,  422,  464,  1298,  460,  1302,  460,  418,  464,  416,  484,  1276,  458,  1302,  460,  1302,  456,  1304,  458,  1300,  452,  428,  452,  430,  452,  428,  454,  426,  452,  428,  452,  428,  452,  426,  452,  426,  452,  1310,  452,  426,  450,  428,  452,  426,  452,  432,  450,  430,  450,  432,  450}}
};



// ======================== 【2. 组合/定时指令定义】 ========================
#define SECONDS(s) ((uint32_t)(s) * 1000UL)
#define MINUTES(m) ((uint32_t)(m) * 60 * 1000UL)
#define HOURS(h) ((uint32_t)(h) * 60 * 60 * 1000UL)
struct SeqStep {const char* cmdName; uint32_t delayAfter;};
struct SequenceCommand {const char* seqName; std::vector<SeqStep> steps;};
const std::vector<SequenceCommand> seqCmdList = {
{"洗屁股",{            {"步骤1", 4000UL},
            {"步骤2", 4000UL},
            {"步骤2", 30000UL},
            {"关闭", 0UL}}}
};
// ==============================================================================





const uint8_t kIrLed = 4;
const uint16_t IR_CARRIER_FREQ = 36800;
IRsend irsend(kIrLed);
WebServer server(8051);



// ======================== 【智能状态灯指示模块】 ========================
// 编译时自动识别开发板型号，实现一码多端兼容
void initStatusLED() {
#if CONFIG_IDF_TARGET_ESP32C6
    // ESP32-C6: 官方板载 WS2812 RGB (通常在 GPIO 8)
    // neopixelWrite 底层自动接管引脚，不需要 pinMode
#elif CONFIG_IDF_TARGET_ESP32C3
    // ESP32-C3: 你的旧代码逻辑 (GPIO 8，低电平点亮)
    pinMode(8, OUTPUT);
    digitalWrite(8, HIGH); // 默认灭
#elif CONFIG_IDF_TARGET_ESP32S3
    // ESP32-S3: 你的旧代码逻辑 (内置 LED，高电平点亮)
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, LOW); // 默认灭
#else
    // 其他常规 ESP32 (兜底)
    #ifndef LED_BUILTIN
    #define LED_BUILTIN 2
    #endif
    pinMode(LED_BUILTIN, OUTPUT);
    digitalWrite(LED_BUILTIN, LOW);
#endif
}

void setStatusLED(bool turnOn) {
#if CONFIG_IDF_TARGET_ESP32C6
    // C6: 亮蓝色(亮度64防刺眼)，灭全黑
    if (turnOn) neopixelWrite(8, 0, 0, 64);
    else        neopixelWrite(8, 0, 0, 0);
#elif CONFIG_IDF_TARGET_ESP32C3
    // C3: 低电平亮，高电平灭
    digitalWrite(8, turnOn ? LOW : HIGH);
#elif CONFIG_IDF_TARGET_ESP32S3
    // S3: 高电平亮，低电平灭
    digitalWrite(LED_BUILTIN, turnOn ? HIGH : LOW);
#else
    digitalWrite(LED_BUILTIN, turnOn ? HIGH : LOW);
#endif
}
// ======================================================================


// ======================== wifi相关 ========================
const unsigned long connectTimeout = 20;
const unsigned long configPortalTimeout = 60;
const unsigned long reconnectDelay = 5000;
unsigned long lastReconnectAttempt = 0;
WiFiManager wm;


void wifiSetup()
{
  Serial.println("Connecting WiFi...");
  wm.setConnectTimeout(connectTimeout);
  wm.setConfigPortalTimeout(configPortalTimeout);
  wm.setBreakAfterConfig(true);
  wm.setCleanConnect(true);
  bool res = wm.autoConnect(apName.c_str(), "12345678");
  if (!res)
  {
    Serial.println("初始连接失败，正在重启...");
    ESP.restart();
  }
  else
  {
    Serial.println("已成功连接 WiFi!");
    setStatusLED(false);
  }
}

void wifiLoop()
{
  if (WiFi.status() != WL_CONNECTED)
  {
    setStatusLED(true);
    unsigned long currentMillis = millis();
    if (currentMillis - lastReconnectAttempt >= reconnectDelay)
    {
      lastReconnectAttempt = currentMillis;
      Serial.println("WiFi 断开，正在尝试重连...");
      bool res = wm.autoConnect(apName.c_str(), "12345678");
      if (!res)
      {
        Serial.println("重连失败，将重启设备...");
        delay(1000);
        ESP.restart();
      }
      else
      {
        Serial.println("重连成功 :)");
        setStatusLED(false);
      }
    }
  }
}
// ======================================================




// ======================== 【3. 非阻塞异步任务引擎】 ========================
bool isTaskRunning = false;
std::vector<SeqStep> activeTaskSteps;
size_t currentStepIdx = 0;
unsigned long lastStepTime = 0;
uint32_t currentWaitDelay = 0;

// 根据名称找红外数据并发射
bool sendRawByName(const char* name) {
    for (const auto& rawCmd : rawCmdList) {
        if (String(name) == String(rawCmd.cmdName)) {
            Serial.print("【发射红外】 -> ");
            Serial.println(rawCmd.cmdName);
            irsend.sendRaw(rawCmd.rawData.data(), rawCmd.rawData.size(), IR_CARRIER_FREQ);
            return true;
        }
    }
    Serial.print("【错误】未找到名字为 '");
    Serial.print(name);
    Serial.println("' 的红外波形数据！");
    return false;
}

// 接收 HTTP 指令处理函数
void handleACIR()
{
    String cmd = server.arg("cmd");
    bool matchFound = false;
    std::vector<SeqStep> newSteps;

    // 1. 先去组合指令列表寻找
    for (const auto& seq : seqCmdList) {
        if (cmd == String(seq.seqName)) {
            newSteps = seq.steps;
            matchFound = true;
            break;
        }
    }

    // 2. 如果组合指令没找到，再去单条指令列表寻找
    if (!matchFound) {
        for (const auto& raw : rawCmdList) {
            if (cmd == String(raw.cmdName)) {
                // 如果是单条指令，直接当作只包含 1 个步骤且延迟为 0 的任务
                newSteps.push_back({raw.cmdName, 0});
                matchFound = true;
                break;
            }
        }
    }

    if (matchFound) {
        // 装载新任务（会自动覆盖/打断当前正在执行的旧任务）
        activeTaskSteps = newSteps;
        currentStepIdx = 0;
        lastStepTime = millis();
        currentWaitDelay = 888; // 收到 HTTP 请求后延迟 888ms 再发第一条，确保 HTTP 响应先顺利发回
        isTaskRunning = true;

        String okJson = R"({"success":true,"cmd":")" + cmd + R"(","msg":"指令/组合已启动"})";
        server.send(200, "application/json", okJson);
    } else {
        String errJson = R"({"success":false,"msg":" 未知 cmd 指令 "})";
        server.send(400, "application/json", errJson);
    }
}

void setup()
{
    Serial.begin(115200);
    delay(200);

    initStatusLED();
    setStatusLED(true); // 通电直接亮灯

    wifiSetup();
    delay(200);
    irsend.begin();
    delay(200);

    server.on(controllerPath.c_str(), handleACIR);
    server.begin();
    Serial.println("HTTP 服务器已启动，端口: 8051");
}

void loop()
{
    wifiLoop();
    server.handleClient();

    // 异步任务调度核心：完全不打断 loop，不阻塞 WiFi
    if (isTaskRunning) {
        if (millis() - lastStepTime >= currentWaitDelay) {
            if (currentStepIdx < activeTaskSteps.size()) {
                // 1. 取出当前步骤
                SeqStep step = activeTaskSteps[currentStepIdx];

                // 2. 发射红外
                sendRawByName(step.cmdName);
                delay(66);
                sendRawByName(step.cmdName);
                delay(66);
                sendRawByName(step.cmdName);

                // 3. 记录时间，准备进入下一个等待期
                lastStepTime = millis();
                currentWaitDelay = step.delayAfter;
                currentStepIdx++;

                if (currentWaitDelay > 0) {
                    Serial.print("【定时任务】等待中... 预计 ");
                    Serial.print(currentWaitDelay / 1000);
                    Serial.println(" 秒后执行下一个动作");
                }
            } else {
                // 所有步骤执行完毕
                isTaskRunning = false;
                Serial.println("【定时任务】当前序列全部执行完毕！");
            }
        }
    }
}











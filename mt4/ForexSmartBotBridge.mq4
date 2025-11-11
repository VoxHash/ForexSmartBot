//+------------------------------------------------------------------+
//|                                                ForexSmartBotBridge|
//|                                     File-based bridge for MT4 <-> Py  |
//+------------------------------------------------------------------+
#property copyright "VoxHash Technologies"
#property link      "https://github.com/voxhash/forexsmartbot"
#property version   "1.00"
#property strict

// External parameters
extern string ServerHost = "127.0.0.1";
extern int    ServerPort = 5555;
extern bool   EnableLogging = true;

// Global variables
string g_log_prefix = "[ForexSmartBotBridge] ";

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    if (EnableLogging)
        Print(g_log_prefix + "ForexSmartBotBridge EA loaded successfully");
    
    // Enable live trading automatically
    if (!IsTradeAllowed())
    {
        if (EnableLogging)
            Print(g_log_prefix + "Live trading not allowed - please enable in EA properties");
    }
    
    // Set up timer for periodic data updates
    EventSetTimer(1); // Update every 1 second
    
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    EventKillTimer();
    if (EnableLogging)
        Print(g_log_prefix + "ForexSmartBotBridge EA unloaded");
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
    // Check for commands from Python application on every tick for immediate response
    static int last_tick_check = 0;
    int current_tick = (int)GetTickCount();
    
    if (current_tick - last_tick_check > 500) // Check every 500ms on tick
    {
        CheckForCommands();
        last_tick_check = current_tick;
    }
}

//+------------------------------------------------------------------+
//| Check for commands from Python application                       |
//+------------------------------------------------------------------+
void CheckForCommands()
{
    // Use relative path - MT4 will look in the Files directory
    string command_file = "ForexSmartBot_Command.txt";
    
    if (EnableLogging)
        Print(g_log_prefix + "Checking for command file: " + command_file);
    
    // Try to open the file directly
    int file_handle = FileOpen(command_file, FILE_READ|FILE_TXT);
    
    if (file_handle != INVALID_HANDLE)
    {
        if (EnableLogging)
            Print(g_log_prefix + "Command file found and opened successfully");
            
        string command = "";
        while (!FileIsEnding(file_handle))
        {
            command = FileReadString(file_handle);
            if (command != "")
            {
                if (EnableLogging)
                    Print(g_log_prefix + "Read command: " + command);
                ExecuteCommand(command);
            }
        }
        
        // If no commands were read, try reading the entire file content
        if (command == "")
        {
            FileSeek(file_handle, 0, SEEK_SET);
            command = FileReadString(file_handle);
            if (command != "")
            {
                if (EnableLogging)
                    Print(g_log_prefix + "Read single command: " + command);
                ExecuteCommand(command);
            }
        }
        FileClose(file_handle);
        
        // Delete the command file after processing
        FileDelete(command_file);
        if (EnableLogging)
            Print(g_log_prefix + "Command file processed and deleted");
    }
    else
    {
        if (EnableLogging)
            Print(g_log_prefix + "Command file not found or could not be opened. Error: " + IntegerToString(GetLastError()));
    }
}

//+------------------------------------------------------------------+
//| Execute command from Python application                          |
//+------------------------------------------------------------------+
void ExecuteCommand(string command)
{
    if (EnableLogging)
        Print(g_log_prefix + "Executing command: " + command);
    
    // Debug: Check what command we received
    if (EnableLogging)
        Print(g_log_prefix + "Command length: " + IntegerToString(StringLen(command)));
    
    // Parse and execute the command
    if (EnableLogging)
        Print(g_log_prefix + "Checking command: " + command + " for OrderSend");
    
    // Debug: Check if command contains OrderSend
    int orderSendPos = StringFind(command, "OrderSend");
    if (EnableLogging)
        Print(g_log_prefix + "OrderSend position: " + IntegerToString(orderSendPos));
    
    if (orderSendPos >= 0)
    {
        if (EnableLogging)
            Print(g_log_prefix + "Processing OrderSend command: " + command);
            
        // Parse OrderSend command
        // Format: OrderSend(SYMBOL,BUY/SELL,QUANTITY,SL=value,TP=value)
        string parts[];
        StringSplit(command, StringGetChar("(", 0), parts);
        if (ArraySize(parts) >= 2)
        {
            string params = parts[1];
            StringReplace(params, ")", "");
            
            if (EnableLogging)
                Print(g_log_prefix + "Parsed parameters: " + params);
            
            string param_parts[];
            StringSplit(params, StringGetChar(",", 0), param_parts);
            
            if (ArraySize(param_parts) >= 3)
            {
                string symbol = param_parts[0];
                string order_type = param_parts[1];
                double quantity = StrToDouble(param_parts[2]);
                
                if (EnableLogging)
                    Print(g_log_prefix + "Symbol: " + symbol + ", Type: " + order_type + ", Quantity: " + DoubleToStr(quantity, 2));
                
                int type = (order_type == "BUY") ? OP_BUY : OP_SELL;
                double price = (type == OP_BUY) ? MarketInfo(symbol, MODE_ASK) : MarketInfo(symbol, MODE_BID);
                
                if (EnableLogging)
                    Print(g_log_prefix + "Order type: " + IntegerToString(type) + ", Price: " + DoubleToStr(price, 5));
                
                double sl = 0, tp = 0;
                // Parse SL and TP from the remaining parameters
                for (int i = 3; i < ArraySize(param_parts); i++)
                {
                    string param = param_parts[i];
                    if (StringFind(param, "SL=") >= 0)
                    {
                        StringReplace(param, "SL=", "");
                        sl = StrToDouble(param);
                        if (EnableLogging)
                            Print(g_log_prefix + "Parsed SL: " + DoubleToStr(sl, 5));
                    }
                    else if (StringFind(param, "TP=") >= 0)
                    {
                        StringReplace(param, "TP=", "");
                        tp = StrToDouble(param);
                        if (EnableLogging)
                            Print(g_log_prefix + "Parsed TP: " + DoubleToStr(tp, 5));
                    }
                }
                
                // Always set SL and TP if not provided
                if (sl == 0) {
                    // Set default SL: 2% from entry price
                    if (type == OP_BUY) {
                        sl = price * 0.98; // 2% below entry for BUY
                    } else {
                        sl = price * 1.02; // 2% above entry for SELL
                    }
                    if (EnableLogging)
                        Print(g_log_prefix + "Default SL set: " + DoubleToStr(sl, 5));
                }
                if (tp == 0) {
                    // Set default TP: 3% from entry price
                    if (type == OP_BUY) {
                        tp = price * 1.03; // 3% above entry for BUY
                    } else {
                        tp = price * 0.97; // 3% below entry for SELL
                    }
                    if (EnableLogging)
                        Print(g_log_prefix + "Default TP set: " + DoubleToStr(tp, 5));
                }
                
                // Execute the order with proper OrderSend syntax
                // OrderSend(symbol, cmd, volume, price, slippage, stoploss, takeprofit, comment, magic, expiration, color)
                if (EnableLogging)
                    Print(g_log_prefix + "Executing OrderSend: " + symbol + ", " + IntegerToString(type) + ", " + DoubleToStr(quantity, 2) + ", " + DoubleToStr(price, 5) + ", SL=" + DoubleToStr(sl, 5) + ", TP=" + DoubleToStr(tp, 5));
                
                int ticket = OrderSend(symbol, type, quantity, price, 3, sl, tp, "ForexSmartBot", 0, 0, clrNONE);
                
                if (ticket > 0)
                {
                    if (EnableLogging)
                        Print(g_log_prefix + "Order executed successfully: " + IntegerToString(ticket) + " for " + symbol);
                }
                else
                {
                    int error = GetLastError();
                    if (EnableLogging)
                        Print(g_log_prefix + "Order failed for " + symbol + ": Error " + IntegerToString(error));
                }
            }
            else
            {
                if (EnableLogging)
                    Print(g_log_prefix + "OrderSend command has insufficient parameters");
            }
        }
        else
        {
            if (EnableLogging)
                Print(g_log_prefix + "OrderSend command parsing failed");
        }
    }
    else if (StringFind(command, "CloseAll") >= 0)
    {
        // Parse CloseAll command
        // Format: CloseAll(SYMBOL)
        string parts[];
        StringSplit(command, StringGetChar("(", 0), parts);
        if (ArraySize(parts) >= 2)
        {
            string params = parts[1];
            StringReplace(params, ")", "");
            StringReplace(params, "(", "");
            
            bool result = CloseAllPositions(params);
            if (EnableLogging)
                Print(g_log_prefix + "CloseAll result: " + (result ? "Success" : "Failed"));
        }
    }
    else if (StringFind(command, "GetBalance") >= 0)
    {
        // Get account balance and write to response file
        double balance = AccountBalance();
        string response_file = "ForexSmartBot_Balance.txt";
        
        int file_handle = FileOpen(response_file, FILE_WRITE|FILE_TXT);
        if (file_handle != INVALID_HANDLE)
        {
            FileWrite(file_handle, DoubleToStr(balance, 2));
            FileClose(file_handle);
            if (EnableLogging)
                Print(g_log_prefix + "Balance written: " + DoubleToStr(balance, 2));
        }
    }
    else if (StringFind(command, "GetPositions") >= 0)
    {
        // Get all positions and write to response file
        string positions = GetOpenPositions();
        string response_file = "ForexSmartBot_Positions.txt";
        
        int file_handle = FileOpen(response_file, FILE_WRITE|FILE_TXT);
        if (file_handle != INVALID_HANDLE)
        {
            FileWrite(file_handle, positions);
            FileClose(file_handle);
            if (EnableLogging)
                Print(g_log_prefix + "Positions written to file");
        }
    }
    else if (StringFind(command, "GetPrice") >= 0)
    {
        // Parse GetPrice command: GetPrice(EURUSD)
        string parts[];
        StringSplit(command, StringGetChar("(", 0), parts);
        if (ArraySize(parts) >= 2)
        {
            string symbol = parts[1];
            StringReplace(symbol, ")", "");
            
            // Get current price for the symbol
            double price = MarketInfo(symbol, MODE_BID);
            if (price > 0)
            {
                string response_file = "ForexSmartBot_Price.txt";
                
                int file_handle = FileOpen(response_file, FILE_WRITE|FILE_TXT);
                if (file_handle != INVALID_HANDLE)
                {
                    FileWrite(file_handle, DoubleToStr(price, 5));
                    FileClose(file_handle);
                    if (EnableLogging)
                        Print(g_log_prefix + "Price written for " + symbol + ": " + DoubleToStr(price, 5));
                }
            }
        }
    }
}

//+------------------------------------------------------------------+
//| Timer function                                                   |
//+------------------------------------------------------------------+
void OnTimer()
{
    // Check for commands from Python application every 1 second for faster response
    static int last_check = 0;
    int current_time = (int)GetTickCount();
    
    if (current_time - last_check > 1000) // Check every 1 second
    {
        CheckForCommands();
        last_check = current_time;
    }
    
    // Log that the EA is running every ~10 seconds with VERSION 2.1 identifier
    if (EnableLogging && MathMod((int)GetTickCount(), 10000) < 1000)
        Print(g_log_prefix + "EA VERSION 2.1 running - Host: " + ServerHost + ", Port: " + IntegerToString(ServerPort));
}

//+------------------------------------------------------------------+
//| Get current price for a symbol                                  |
//+------------------------------------------------------------------+
double GetCurrentPrice(string symbol)
{
    if (symbol == "")
        symbol = Symbol();
    
    return MarketInfo(symbol, MODE_BID);
}

//+------------------------------------------------------------------+
//| Get account balance                                             |
//+------------------------------------------------------------------+
double GetAccountBalance()
{
    return AccountBalance();
}

//+------------------------------------------------------------------+
//| Get account equity                                              |
//+------------------------------------------------------------------+
double GetAccountEquity()
{
    return AccountEquity();
}

//+------------------------------------------------------------------+
//| Get symbol information                                          |
//+------------------------------------------------------------------+
string GetSymbolInfo(string symbol)
{
    if (symbol == "")
        symbol = Symbol();
    
    string info = "";
    info += "Symbol: " + symbol + "\n";
    info += "Bid: " + DoubleToStr(MarketInfo(symbol, MODE_BID), Digits) + "\n";
    info += "Ask: " + DoubleToStr(MarketInfo(symbol, MODE_ASK), Digits) + "\n";
    info += "Spread: " + DoubleToStr(MarketInfo(symbol, MODE_SPREAD), 0) + "\n";
    info += "Digits: " + IntegerToString((int)MarketInfo(symbol, MODE_DIGITS)) + "\n";
    info += "Point: " + DoubleToStr(MarketInfo(symbol, MODE_POINT), Digits) + "\n";
    
    return info;
}

//+------------------------------------------------------------------+
//| Get historical data for a symbol                                |
//+------------------------------------------------------------------+
string GetHistoricalData(string symbol, int timeframe, int bars)
{
    if (symbol == "")
        symbol = Symbol();
    
    string data = "";
    for (int i = 0; i < bars && i < Bars; i++)
    {
        data += TimeToStr(Time[i]) + ",";
        data += DoubleToStr(Open[i], Digits) + ",";
        data += DoubleToStr(High[i], Digits) + ",";
        data += DoubleToStr(Low[i], Digits) + ",";
        data += DoubleToStr(Close[i], Digits) + ",";
        data += DoubleToStr(Volume[i], 0) + "\n";
    }
    
    return data;
}

//+------------------------------------------------------------------+
//| Submit order to MT4                                              |
//+------------------------------------------------------------------+
int SubmitOrder(string symbol, int side, double volume, double sl = 0, double tp = 0)
{
    int ticket = -1;
    int order_type = (side > 0) ? OP_BUY : OP_SELL;
    double price = (side > 0) ? MarketInfo(symbol, MODE_ASK) : MarketInfo(symbol, MODE_BID);
    
    // Normalize volume to lot size
    double lot_size = MarketInfo(symbol, MODE_LOTSIZE);
    double min_lot = MarketInfo(symbol, MODE_MINLOT);
    double max_lot = MarketInfo(symbol, MODE_MAXLOT);
    
    if (volume < min_lot) volume = min_lot;
    if (volume > max_lot) volume = max_lot;
    
    // Submit the order
    ticket = OrderSend(symbol, order_type, volume, price, 3, sl, tp, "ForexSmartBot", 0, 0, clrNONE);
    
    if (ticket > 0)
    {
        if (EnableLogging)
            Print(g_log_prefix + "Order submitted: " + IntegerToString(ticket) + " " + symbol + " " + DoubleToStr(volume, 2));
    }
    else
    {
        if (EnableLogging)
            Print(g_log_prefix + "Order failed: " + symbol + " Error: " + IntegerToString(GetLastError()));
    }
    
    return ticket;
}

//+------------------------------------------------------------------+
//| Close all positions for a symbol                                 |
//+------------------------------------------------------------------+
bool CloseAllPositions(string symbol)
{
    bool success = true;
    
    for (int i = OrdersTotal() - 1; i >= 0; i--)
    {
        if (OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
        {
            if (OrderSymbol() == symbol)
            {
                double price = (OrderType() == OP_BUY) ? MarketInfo(symbol, MODE_BID) : MarketInfo(symbol, MODE_ASK);
                bool result = OrderClose(OrderTicket(), OrderLots(), price, 3, clrNONE);
                if (!result)
                {
                    success = false;
                    if (EnableLogging)
                        Print(g_log_prefix + "Failed to close order: " + IntegerToString(OrderTicket()) + " Error: " + IntegerToString(GetLastError()));
                }
                else
                {
                    if (EnableLogging)
                        Print(g_log_prefix + "Order closed: " + IntegerToString(OrderTicket()));
                }
            }
        }
    }
    
    return success;
}

//+------------------------------------------------------------------+
//| Get all open positions                                           |
//+------------------------------------------------------------------+
string GetOpenPositions()
{
    string positions = "[";
    bool first = true;
    
    for (int i = 0; i < OrdersTotal(); i++)
    {
        if (OrderSelect(i, SELECT_BY_POS, MODE_TRADES))
        {
            if (!first) positions += ",";
            first = false;
            
            positions += "{";
            positions += "\"ticket\":" + IntegerToString(OrderTicket()) + ",";
            positions += "\"symbol\":\"" + OrderSymbol() + "\",";
            positions += "\"type\":" + IntegerToString(OrderType()) + ",";
            positions += "\"side\":" + IntegerToString((OrderType() == OP_BUY) ? 1 : -1) + ",";
            positions += "\"volume\":" + DoubleToStr(OrderLots(), 2) + ",";
            positions += "\"entry_price\":" + DoubleToStr(OrderOpenPrice(), Digits) + ",";
            positions += "\"current_price\":" + DoubleToStr((OrderType() == OP_BUY) ? MarketInfo(OrderSymbol(), MODE_BID) : MarketInfo(OrderSymbol(), MODE_ASK), Digits) + ",";
            positions += "\"sl\":" + DoubleToStr(OrderStopLoss(), Digits) + ",";
            positions += "\"tp\":" + DoubleToStr(OrderTakeProfit(), Digits) + ",";
            positions += "\"profit\":" + DoubleToStr(OrderProfit(), 2) + ",";
            positions += "\"timestamp\":\"" + TimeToStr(OrderOpenTime()) + "\"";
            positions += "}";
        }
    }
    
    positions += "]";
    return positions;
}

//+------------------------------------------------------------------+
//| Custom function to simulate ZeroMQ responses                     |
//+------------------------------------------------------------------+
string SimulateZeroMQResponse(string command)
{
    string response = "";
    
    if (command == "ping")
    {
        response = "{\"status\": \"ok\", \"message\": \"pong\"}";
    }
    else if (command == "price")
    {
        double price = GetCurrentPrice(Symbol());
        response = "{\"price\": " + DoubleToStr(price, Digits) + "}";
    }
    else if (command == "balance")
    {
        double balance = GetAccountBalance();
        response = "{\"balance\": " + DoubleToStr(balance, 2) + "}";
    }
    else if (command == "equity")
    {
        double equity = GetAccountEquity();
        response = "{\"equity\": " + DoubleToStr(equity, 2) + "}";
    }
    else if (command == "symbol_info")
    {
        string info = GetSymbolInfo(Symbol());
        response = "{\"info\": \"" + info + "\"}";
    }
    else if (command == "historical_data")
    {
        string data = GetHistoricalData(Symbol(), PERIOD_H1, 100);
        response = "{\"data\": \"" + data + "\"}";
    }
    else if (command == "order")
    {
        // This would be called with order parameters
        // For now, just return a success response
        response = "{\"order_id\": " + IntegerToString(GetTickCount()) + ", \"status\": \"success\"}";
    }
    else if (command == "close_all")
    {
        bool result = CloseAllPositions(Symbol());
        response = "{\"success\": " + (result ? "true" : "false") + "}";
    }
    else if (command == "positions")
    {
        string positions = GetOpenPositions();
        response = "{\"positions\": " + positions + "}";
    }
    else
    {
        response = "{\"error\": \"Unknown command: " + command + "\"}";
    }
    
    return response;
}

//+------------------------------------------------------------------+
//| Note: This is a simplified version for demonstration            |
//| In production, you would need a proper ZeroMQ implementation    |
//| or use a third-party MT4-Python bridge library                  |
//+------------------------------------------------------------------+
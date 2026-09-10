Attribute VB_Name = "AlertWorkbookVBA"
' ============================================================
' TRADE ANOMALY ALERT WORKBOOK - VBA MACROS
' ============================================================

Option Explicit

Sub UpdateAlertWorkbook()
    '
    ' Main macro: Import flagged_trades.csv and format
    '
    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual
    
    On Error GoTo ErrorHandler
    
    Call ClearPreviousData
    Call ImportFlaggedTrades
    Call GenerateSummary
    Call FormatSheets
    Call AddTimestamp
    
    Application.ScreenUpdating = True
    Application.Calculation = xlCalculationAutomatic
    
    MsgBox "✓ Alert workbook updated successfully", vbInformation
    Exit Sub
    
ErrorHandler:
    MsgBox "Error: " & Err.Description, vbCritical
    Application.ScreenUpdating = True
    Application.Calculation = xlCalculationAutomatic
End Sub

Sub ClearPreviousData()
    '
    ' Clear previous data from Flagged Trades sheet
    '
    Dim ws As Worksheet
    Set ws = ThisWorkbook.Sheets("Flagged Trades")
    
    ws.UsedRange.Delete Shift:=xlUp
    
End Sub

Sub ImportFlaggedTrades()
    '
    ' Import flagged_trades.csv into Excel
    '
    Dim ws As Worksheet
    Dim filePath As String
    
    Set ws = ThisWorkbook.Sheets("Flagged Trades")
    
    ' Modify this path to where trade_monitoring_flagged.csv is saved
    filePath = ThisWorkbook.Path & "\trade_monitoring_flagged.csv"
    If Dir(filePath) = "" Then
        filePath = ThisWorkbook.Path & "\outputs\flagged_trades.csv"
    End If
    
    ' Check if file exists
    If Dir(filePath) = "" Then
        MsgBox "File not found: " & filePath, vbExclamation
        Exit Sub
    End If
    
    ' Use QueryTable to import CSV
    With ws.QueryTables.Add(Connection:="TEXT;" & filePath, Destination:=ws.Range("A1"))
        .TextFileCommaDelimited = True
        .TextFileFirstRowHasHeaders = True
        .Refresh BackgroundQuery:=False
    End With
    
End Sub

Sub GenerateSummary()
    '
    ' Calculate and populate summary KPIs on Summary sheet
    '
    Dim ws_summary As Worksheet
    Dim ws_flagged As Worksheet
    Dim lastRow As Long
    
    Set ws_summary = ThisWorkbook.Sheets("Summary")
    Set ws_flagged = ThisWorkbook.Sheets("Flagged Trades")
    
    lastRow = ws_flagged.Cells(ws_flagged.Rows.Count, 1).End(xlUp).Row
    
    Dim totalFlagged As Long, highSeverity As Long, mediumSeverity As Long
    Dim totalRisk As Double
    
    If lastRow < 2 Then
        totalFlagged = 0
        highSeverity = 0
        mediumSeverity = 0
        totalRisk = 0
    Else
        totalFlagged = lastRow - 1  ' Exclude header
        highSeverity = Application.WorksheetFunction.CountIf(ws_flagged.Range("H:H"), "HIGH")
        mediumSeverity = Application.WorksheetFunction.CountIf(ws_flagged.Range("H:H"), "MEDIUM")
        
        totalRisk = Application.WorksheetFunction.SumProduct( _
            ws_flagged.Range("C2:C" & lastRow), _
            ws_flagged.Range("D2:D" & lastRow))
    End If
    
    ' Populate summary sheet
    ws_summary.Range("B2").Value = totalFlagged & " trades"
    ws_summary.Range("B3").Value = highSeverity & " trades"
    ws_summary.Range("B4").Value = mediumSeverity & " trades"
    ws_summary.Range("B5").Value = Format(totalRisk, "$#,##0.00")
    
End Sub

Sub FormatSheets()
    '
    ' Apply formatting to Flagged Trades sheet
    '
    Dim ws As Worksheet
    Dim lastRow As Long, lastCol As Long
    Dim i As Long
    
    Set ws = ThisWorkbook.Sheets("Flagged Trades")
    
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    lastCol = ws.Cells(1, ws.Columns.Count).End(xlToLeft).Column
    
    If lastRow < 2 Then Exit Sub
    
    ' Format header row
    With ws.Range(ws.Cells(1, 1), ws.Cells(1, lastCol))
        .Font.Bold = True
        .Interior.Color = RGB(70, 130, 180)  ' Steel blue
        .Font.Color = RGB(255, 255, 255)  ' White
        .HorizontalAlignment = xlCenter
    End With
    
    ' Auto-fit columns
    ws.Columns("A:I").AutoFit
    
    ' Freeze header row
    ws.Range("A2").Select
    ActiveWindow.FreezePanes = True
    
    ' Apply conditional formatting (color by severity)
    Dim severityCol As Long
    severityCol = 8  ' Column H (Severity)
    
    For i = 2 To lastRow
        Select Case ws.Cells(i, severityCol).Value
            Case "HIGH"
                ws.Range(ws.Cells(i, 1), ws.Cells(i, lastCol)).Interior.Color = RGB(255, 220, 220)  ' Soft Red
                ws.Range(ws.Cells(i, 1), ws.Cells(i, lastCol)).Font.Color = RGB(150, 0, 0)
            Case "MEDIUM"
                ws.Range(ws.Cells(i, 1), ws.Cells(i, lastCol)).Interior.Color = RGB(255, 235, 200)  ' Soft Orange
                ws.Range(ws.Cells(i, 1), ws.Cells(i, lastCol)).Font.Color = RGB(150, 80, 0)
            Case "LOW"
                ws.Range(ws.Cells(i, 1), ws.Cells(i, lastCol)).Interior.Color = RGB(255, 255, 220)  ' Soft Yellow
                ws.Range(ws.Cells(i, 1), ws.Cells(i, lastCol)).Font.Color = RGB(100, 100, 0)
        End Select
    Next i
    
    ' Format numeric columns
    ws.Range("C2:C" & lastRow).NumberFormat = "#,##0"  ' Quantity
    ws.Range("D2:D" & lastRow).NumberFormat = "$#,##0.00"  ' Price
    ws.Range("I2:I" & lastRow).NumberFormat = "0.00%"  ' Anomaly score
    
End Sub

Sub AddTimestamp()
    '
    ' Add last-updated timestamp
    '
    Dim ws As Worksheet
    Set ws = ThisWorkbook.Sheets("Summary")
    
    ws.Range("B10").Value = "Last Updated:"
    ws.Range("C10").Value = Now()
    ws.Range("C10").NumberFormat = "yyyy-mm-dd hh:mm:ss"
    
End Sub

' ============================================================
' BUTTON ACTIONS (Attach to Excel buttons)
' ============================================================

Sub ButtonRefresh_Click()
    Call UpdateAlertWorkbook
End Sub

Sub ButtonExportToCSV_Click()
    '
    ' Export flagged trades to CSV for external use
    '
    Dim ws As Worksheet
    Dim filePath As String
    
    Set ws = ThisWorkbook.Sheets("Flagged Trades")
    filePath = ThisWorkbook.Path & "\flagged_trades_export_" & Format(Now(), "yyyymmdd_hhmmss") & ".csv"
    
    ' Copy and paste as CSV
    ws.SaveAs filePath, xlCSV
    MsgBox "✓ Exported to: " & filePath, vbInformation
    
End Sub

Sub ButtonOpenDashboard_Click()
    '
    ' Open Tableau dashboard
    '
    Dim dashboardURL As String
    dashboardURL = "https://YOUR_TABLEAU_SERVER/views/TradeMonitoring/Dashboard"
    
    CreateObject("Shell.Application").Open dashboardURL
    
End Sub

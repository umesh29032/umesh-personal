// Trigger function to run on edit
function onEdit(e) {
  const sheet = e.source.getActiveSheet();
  const range = e.range;
  const data = sheet.getDataRange().getValues();
  const row = range.getRow();
  const col = range.getColumn();
  const value = range.getValue();

  // Automatically calculate bills when editing item details
  if (col >= 1 && col <= 6 && row <= data.length && !isTotalRow(data[row - 1]) && !isHeaderRow(data[row - 1])) {
    calculateBills();
  }

  // Detect new bill addition (e.g., entering "BILL X" in column A)
  if (col === 1 && value.toString().toUpperCase().startsWith("BILL") && !isExistingBill(data, row)) {
    addNewBillAdvanced(row);
  }
}

// Helper function to check if a row is a total row
function isTotalRow(rowData) {
  if (!rowData) return false;
  const firstCell = rowData[0]?.toString().toUpperCase() || '';
  return firstCell && (firstCell.includes("TOTAL") || firstCell.includes("GRAND"));
}

// Helper function to check if a row is a header row
function isHeaderRow(rowData) {
  if (!rowData) return false;
  const firstCell = rowData[0]?.toString().toUpperCase() || '';
  return firstCell === "ITEM NAME";
}

// Helper function to check if a bill already exists
function isExistingBill(data, row) {
  if (!data || !data.length) return false;
  return data.some((rowData, index) => {
    if (index >= row - 1) return false;
    return rowData[0]?.toString().toUpperCase().startsWith("BILL");
  });
}

// Main calculation function
function calculateBills() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const data = sheet.getDataRange().getValues();
  
  let sgstTotalAll = 0;
  let cgstTotalAll = 0;
  let withoutGstTotalAll = 0;
  let withGstTotalAll = 0;
  
  console.log("Starting bill calculation...");
  
  // First pass: Process each bill and collect totals
  let bills = [];
  for (let i = 0; i < data.length; i++) {
    const row = data[i];
    if (!row) continue;
    
    const firstCell = (row[0]?.toString() || '').trim().toUpperCase();
    if (firstCell.startsWith("BILL")) {
      // Found a bill, track its position
      const billStart = i;
      let billEnd = -1;
      
      // Find the end of this bill
      for (let j = i + 1; j < data.length; j++) {
        if (j >= data.length) break;
        
        const nextRowCell = (data[j][0]?.toString() || '').trim().toUpperCase();
        if (nextRowCell.startsWith("BILL") || nextRowCell.includes("GRAND TOTAL")) {
          billEnd = j - 1;
          break;
        }
        
        // If we reach the end of the data, set the end row to the last row
        if (j === data.length - 1) {
          billEnd = j;
        }
      }
      
      if (billEnd !== -1) {
        bills.push({ start: billStart, end: billEnd, name: firstCell });
        console.log(`Found bill: ${firstCell} from row ${billStart+1} to ${billEnd+1}`);
        // Skip to the end of this bill to avoid processing it twice
        i = billEnd;
      }
    }
  }
  
  console.log(`Found ${bills.length} bills to process`);
  
  // Second pass: Process each bill and update totals
  for (const bill of bills) {
    const [sgst, cgst, withoutGst, withGst] = processBill(sheet, data, bill.start, bill.end);
    sgstTotalAll += sgst;
    cgstTotalAll += cgst;
    withoutGstTotalAll += withoutGst;
    withGstTotalAll += withGst;
    
    console.log(`Processed ${bill.name}: SGST=${sgst}, CGST=${cgst}, Without GST=${withoutGst}, With GST=${withGst}`);
  }
  
  console.log(`Grand Totals: SGST=${sgstTotalAll}, CGST=${cgstTotalAll}, Without GST=${withoutGstTotalAll}, With GST=${withGstTotalAll}`);
  
  // Update grand total section
  let grandTotalRow = -1;
  for (let i = 0; i < data.length; i++) {
    const cellValue = (data[i][0]?.toString() || '').trim().toUpperCase();
    if (cellValue.includes("GRAND TOTAL")) {
      grandTotalRow = i;
      break;
    }
  }
  
  if (grandTotalRow !== -1) {
    // Find and update each grand total row
    for (let i = grandTotalRow + 1; i < Math.min(grandTotalRow + 10, data.length); i++) {
      if (i >= data.length) break;
      
      const rowText = (data[i][0]?.toString() || '').trim().toUpperCase();
      
      if (rowText.includes("ALL BILLS TOTAL SGST:")) {
        sheet.getRange(i + 1, 10).setValue(sgstTotalAll.toFixed(2));
        console.log(`Updated ALL BILLS TOTAL SGST: ${sgstTotalAll.toFixed(2)} at row ${i+1}`);
      } else if (rowText.includes("ALL BILLS TOTAL CGST:")) {
        sheet.getRange(i + 1, 10).setValue(cgstTotalAll.toFixed(2));
        console.log(`Updated ALL BILLS TOTAL CGST: ${cgstTotalAll.toFixed(2)} at row ${i+1}`);
      } else if (rowText.includes("ALL BILLS TOTAL WITHOUT GST:")) {
        sheet.getRange(i + 1, 10).setValue(withoutGstTotalAll.toFixed(2));
        console.log(`Updated ALL BILLS TOTAL WITHOUT GST: ${withoutGstTotalAll.toFixed(2)} at row ${i+1}`);
      } else if (rowText.includes("ALL BILLS TOTAL WITH GST:")) {
        sheet.getRange(i + 1, 10).setValue(withGstTotalAll.toFixed(2));
        console.log(`Updated ALL BILLS TOTAL WITH GST: ${withGstTotalAll.toFixed(2)} at row ${i+1}`);
      }
    }
  } else {
    console.warn("Grand total row not found. Skipping grand total updates.");
  }
  
  console.log("Bill calculation completed successfully");
}

// Process a single bill and return its totals
function processBill(sheet, data, startRow, endRow) {
  let sgstTotal = 0;
  let cgstTotal = 0;
  let withoutGstTotal = 0;
  let withGstTotal = 0;
  
  console.log(`Processing bill from row ${startRow+1} to ${endRow+1}`);
  
  // Skip the bill header and column header rows
  let itemStartRow = startRow + 2;
  
  // Find where the totals start by looking for "Total SGST:" row
  let totalRowIndex = -1;
  for (let i = startRow; i <= endRow; i++) {
    const firstCell = (data[i][0]?.toString() || '').trim().toUpperCase();
    if (firstCell === "TOTAL SGST:") {
      totalRowIndex = i;
      break;
    }
  }
  
  // If we can't find total rows, we'll assume all rows are items
  const itemEndRow = totalRowIndex !== -1 ? totalRowIndex - 1 : endRow;
  
  console.log(`Item rows range: ${itemStartRow+1} to ${itemEndRow+1}`);
  
  // Process each item row
  for (let i = itemStartRow; i <= itemEndRow; i++) {
    // Skip rows that don't exist in data
    if (i >= data.length) continue;
    
    const row = data[i];
    if (!row || !row[0]) continue;
    
    const firstCell = (row[0].toString() || '').trim().toUpperCase();
    
    // Skip header rows and empty rows
    if (firstCell === "ITEM NAME" || firstCell.startsWith("TOTAL") || firstCell === "") {
      continue;
    }
    
    // Process item calculations
    const qty = parseFloat(row[2]) || 0;
    const rate = parseFloat(row[3]) || 0;
    const sgstPercent = parseFloat(row[4]) || 0;
    const cgstPercent = parseFloat(row[5]) || 0;
    
    const amtWithoutGST = qty * rate;
    const sgstVal = (amtWithoutGST * sgstPercent) / 100;
    const cgstVal = (amtWithoutGST * cgstPercent) / 100;
    const grandTotal = amtWithoutGST + sgstVal + cgstVal;
    
    // Update the sheet with calculated values
    sheet.getRange(i + 1, 7).setValue(amtWithoutGST.toFixed(2));
    sheet.getRange(i + 1, 8).setValue(sgstVal.toFixed(2));
    sheet.getRange(i + 1, 9).setValue(cgstVal.toFixed(2));
    sheet.getRange(i + 1, 10).setValue(grandTotal.toFixed(2));
    
    console.log(`Row ${i+1}: ${firstCell} - Qty: ${qty}, Rate: ${rate}, SGST: ${sgstPercent}%, CGST: ${cgstPercent}%, Amount: ${amtWithoutGST.toFixed(2)}, Total: ${grandTotal.toFixed(2)}`);
    
    // Add to bill totals
    sgstTotal += sgstVal;
    cgstTotal += cgstVal;
    withoutGstTotal += amtWithoutGST;
    withGstTotal += grandTotal;
  }
  
  console.log(`Bill totals: SGST=${sgstTotal.toFixed(2)}, CGST=${cgstTotal.toFixed(2)}, Without GST=${withoutGstTotal.toFixed(2)}, With GST=${withGstTotal.toFixed(2)}`);
  
  // If we found total rows, update them
  if (totalRowIndex !== -1) {
    // Look for each specific total row and update it
    let foundSGST = false;
    let foundCGST = false;
    let foundWithoutGST = false;
    let foundWithGST = false;
    
    // Search from totalRowIndex to the end of this bill
    for (let i = totalRowIndex; i <= endRow; i++) {
      if (i >= data.length) break;
      
      const firstCell = (data[i][0]?.toString() || '').trim().toUpperCase();
      
      if (firstCell === "TOTAL SGST:") {
        sheet.getRange(i + 1, 10).setValue(sgstTotal.toFixed(2));
        console.log(`Updated TOTAL SGST: ${sgstTotal.toFixed(2)} at row ${i+1}`);
        foundSGST = true;
      } else if (firstCell === "TOTAL CGST:") {
        sheet.getRange(i + 1, 10).setValue(cgstTotal.toFixed(2));
        console.log(`Updated TOTAL CGST: ${cgstTotal.toFixed(2)} at row ${i+1}`);
        foundCGST = true;
      } else if (firstCell === "TOTAL WITHOUT GST:") {
        sheet.getRange(i + 1, 10).setValue(withoutGstTotal.toFixed(2));
        console.log(`Updated TOTAL WITHOUT GST: ${withoutGstTotal.toFixed(2)} at row ${i+1}`);
        foundWithoutGST = true;
      } else if (firstCell === "TOTAL WITH GST:") {
        sheet.getRange(i + 1, 10).setValue(withGstTotal.toFixed(2));
        console.log(`Updated TOTAL WITH GST: ${withGstTotal.toFixed(2)} at row ${i+1}`);
        foundWithGST = true;
      }
      
      // If we've found all total rows, we can break
      if (foundSGST && foundCGST && foundWithoutGST && foundWithGST) {
        break;
      }
    }
    
    // If any total rows are missing, log a warning
    if (!foundSGST || !foundCGST || !foundWithoutGST || !foundWithGST) {
      console.warn(`Some total rows are missing for bill ending at row ${endRow+1}`);
    }
  } else {
    console.warn(`No total rows found for bill ending at row ${endRow+1}`);
  }
  
  return [sgstTotal, cgstTotal, withoutGstTotal, withGstTotal];
}

// Advanced function to add a new bill at a specific row
function addNewBillAdvanced(rowNum) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const data = sheet.getDataRange().getValues();
  
  // Default to adding at the end if no row specified
  if (!rowNum) {
    rowNum = data.length + 1;
  }
  
  let insertRow = Math.min(rowNum, data.length + 1); // Ensure insertRow is within bounds
  
  // Ensure insertRow is before grand total
  let grandTotalRow = -1;
  for (let i = 0; i < data.length; i++) {
    if ((data[i][0]?.toString() || '').toUpperCase().includes("GRAND TOTAL")) {
      grandTotalRow = i + 1;
      if (insertRow >= grandTotalRow) {
        insertRow = grandTotalRow;
      }
      break;
    }
  }
  
  // Get bill name from the row or generate a new one
  let billName;
  if (rowNum <= data.length && data[rowNum - 1] && data[rowNum - 1][0]) {
    billName = data[rowNum - 1][0].toString().trim().toUpperCase();
  } else {
    billName = `BILL ${findNextBillNumber(data)}`;
  }
  
  // Updated bill template with the new items and HSN codes
  const billTemplate = [
    [billName, '', '', '', '', '', '', '', '', ''],
    ['Item Name', 'HSN / SAC', 'Quantity', 'Rate (INR)', 'SGST %', 'CGST %', 'Amount Without GST', 'SGST Value', 'CGST Value', 'Grand Total'],
    ['Top set', '6206', 1, 0, 2.5, 2.5, '', '', '', ''],
    ['Suit set', '6203', 1, 0, 2.5, 2.5, '', '', '', ''],
    ['Nicker set', '6203', 1, 0, 2.5, 2.5, '', '', '', ''],
    ['Capri set', '6108', 1, 0, 2.5, 2.5, '', '', '', ''],
    ['Mix hosery goods', '6115', 1, 0, 2.5, 2.5, '', '', '', ''],
    ['', '', '', '', '', '', '', '', '', ''],
    ['Total SGST:', '', '', '', '', '', '', '', '', ''],
    ['Total CGST:', '', '', '', '', '', '', '', '', ''],
    ['Total Without GST:', '', '', '', '', '', '', '', '', ''],
    ['Total With GST:', '', '', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', '', '', '']
  ];
  
  // Insert rows for the bill template in reverse order to maintain structure
  for (let i = billTemplate.length - 1; i >= 0; i--) {
    try {
      sheet.insertRowBefore(insertRow);
      const row = billTemplate[i];
      for (let j = 0; j < row.length; j++) {
        sheet.getRange(insertRow, j + 1).setValue(row[j] || '');
      }
    } catch (e) {
      console.error(`Error inserting row at ${insertRow}: ${e.message}`);
      SpreadsheetApp.getUi().alert(`Error adding bill: ${e.message}`);
      return;
    }
  }
  
  // Apply formatting
  const headerRange = sheet.getRange(insertRow, 1, 1, 10);
  headerRange.setBackground('#4CAF50').setFontColor('white').setFontWeight('bold');
  
  const columnHeaderRange = sheet.getRange(insertRow + 1, 1, 1, 10);
  columnHeaderRange.setBackground('#E8F5E8').setFontWeight('bold');
  
  const totalRange = sheet.getRange(insertRow + 8, 1, 4, 10);
  totalRange.setBackground('#FFF3E0').setFontWeight('bold');
  
  // Recalculate all bills
  calculateBills();
  SpreadsheetApp.getUi().alert(`✅ New bill "${billName}" added successfully!`);
}

// Helper function to find the next bill number
function findNextBillNumber(data) {
  const bills = data
    .filter(row => row[0]?.toString().toUpperCase().startsWith("BILL"))
    .map(row => {
      const match = row[0].toString().match(/\d+/);
      return match ? parseInt(match[0], 10) : 0;
    });
  
  return bills.length > 0 ? Math.max(...bills) + 1 : 1;
}

// Function to delete a specific bill
function deleteBill() {
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const data = sheet.getDataRange().getValues();
  
  const bills = [];
  for (let i = 0; i < data.length; i++) {
    const cell = (data[i][0]?.toString() || '').toUpperCase();
    if (cell && cell.startsWith("BILL")) {
      bills.push({ name: cell, row: i + 1 });
    }
  }
  
  if (bills.length === 0) {
    ui.alert('❌ No bills found to delete!');
    return;
  }
  
  const billNames = bills.map(bill => bill.name).join('\n');
  const billResponse = ui.prompt('Delete Bill', `Enter exact bill name to delete:\n\n${billNames}`, ui.ButtonSet.OK_CANCEL);
  
  if (billResponse.getSelectedButton() == ui.Button.CANCEL) return;
  
  const selectedBill = billResponse.getResponseText().trim().toUpperCase();
  const targetBill = bills.find(bill => bill.name === selectedBill);
  
  if (!targetBill) {
    ui.alert('❌ Bill not found! Please enter exact bill name.');
    return;
  }
  
  const confirmResponse = ui.alert('Confirm Deletion', `Are you sure you want to delete "${selectedBill}"?\nThis action cannot be undone.`, ui.ButtonSet.YES_NO);
  
  if (confirmResponse !== ui.Button.YES) return;
  
  // Find the end of this bill (next bill or grand total)
  let endRow = targetBill.row;
  for (let i = targetBill.row; i < data.length; i++) {
    const cellValue = (data[i][0]?.toString() || '').toUpperCase();
    if (cellValue.includes("GRAND TOTAL") || 
        (cellValue.startsWith("BILL") && i > targetBill.row - 1)) {
      endRow = i;
      break;
    }
    if (i === data.length - 1) {
      endRow = i + 1; // If we reach the end, include the last row
    }
  }
  
  const rowsToDelete = endRow - targetBill.row;
  if (rowsToDelete > 0) {
    sheet.deleteRows(targetBill.row, rowsToDelete);
  }
  
  calculateBills();
  ui.alert(`✅ Bill "${selectedBill}" deleted successfully!`);
}

// Function to edit an existing item
function editItem() {
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const data = sheet.getDataRange().getValues();
  
  const items = [];
  let currentBill = "";
  
  for (let i = 0; i < data.length; i++) {
    const cell = (data[i][0]?.toString() || '').trim();
    
    if (cell.toUpperCase().startsWith("BILL")) {
      currentBill = cell;
      continue;
    }
    
    if (cell && cell.toUpperCase() !== "ITEM NAME" && !isTotalRow(data[i]) && data[i][2] && data[i][3]) {
      items.push({ 
        name: cell, 
        bill: currentBill, 
        row: i + 1,
        hsn: data[i][1],
        qty: data[i][2],
        rate: data[i][3],
        sgst: data[i][4],
        cgst: data[i][5]
      });
    }
  }
  
  if (items.length === 0) {
    ui.alert('❌ No items found to edit!');
    return;
  }
  
  const itemList = items.map(item => `${item.name} (${item.bill})`).join('\n');
  const itemResponse = ui.prompt('Edit Item', `Select item to edit:\n\n${itemList}\n\nEnter exact item name:`, ui.ButtonSet.OK_CANCEL);
  
  if (itemResponse.getSelectedButton() == ui.Button.CANCEL) return;
  
  const selectedItem = itemResponse.getResponseText().trim();
  const targetItem = items.find(item => item.name.toLowerCase() === selectedItem.toLowerCase());
  
  if (!targetItem) {
    ui.alert('❌ Item not found! Please enter exact item name.');
    return;
  }
  
  const currentDetails = `${targetItem.name},${targetItem.hsn},${targetItem.qty},${targetItem.rate},${targetItem.sgst},${targetItem.cgst}`;
  const editResponse = ui.prompt('Edit Item Details', `Current: ${currentDetails}\n\nEnter new details (Format: ItemName,HSN/SAC,Quantity,Rate,SGST%,CGST%):`, ui.ButtonSet.OK_CANCEL);
  
  if (editResponse.getSelectedButton() == ui.Button.CANCEL) return;
  
  const newDetails = editResponse.getResponseText().split(',');
  if (newDetails.length !== 6) {
    ui.alert('❌ Invalid format! Please use: ItemName,HSN/SAC,Quantity,Rate,SGST%,CGST%');
    return;
  }
  
  sheet.getRange(targetItem.row, 1).setValue(newDetails[0].trim());
  sheet.getRange(targetItem.row, 2).setValue(newDetails[1].trim());
  sheet.getRange(targetItem.row, 3).setValue(parseFloat(newDetails[2]) || 0);
  sheet.getRange(targetItem.row, 4).setValue(parseFloat(newDetails[3]) || 0);
  sheet.getRange(targetItem.row, 5).setValue(parseFloat(newDetails[4]) || 0);
  sheet.getRange(targetItem.row, 6).setValue(parseFloat(newDetails[5]) || 0);
  
  calculateBills();
  ui.alert(`✅ Item "${newDetails[0]}" updated successfully!`);
}

// Function to show detailed bill summary with export option
function showBillSummary() {
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const data = sheet.getDataRange().getValues();
  
  let summary = "📊 BILL SUMMARY REPORT\n\n";
  let currentBill = "";
  let billTotal = 0;
  let grandTotal = 0;
  
  for (let i = 0; i < data.length; i++) {
    const cell = (data[i][0]?.toString() || '').trim();
    
    if (cell.toUpperCase().startsWith("BILL")) {
      if (currentBill) {
        summary += `${currentBill}: ₹${billTotal.toFixed(2)}\n`;
        grandTotal += billTotal;
      }
      currentBill = cell;
      billTotal = 0;
      continue;
    }
    
    if (cell.toUpperCase() === "TOTAL WITH GST:" && data[i][9]) {
      billTotal = parseFloat(data[i][9]) || 0;
    }
  }
  
  if (currentBill) {
    summary += `${currentBill}: ₹${billTotal.toFixed(2)}\n`;
    grandTotal += billTotal;
  }
  
  summary += `\n💰 GRAND TOTAL: ₹${grandTotal.toFixed(2)}\n\nGenerated on: ${new Date().toLocaleString()}`;
  
  // Fixed the syntax error in ui.alert by removing the extra comma
  const response = ui.alert('Bill Summary', summary, ui.ButtonSet.OK_CANCEL);
  if (response === ui.Button.OK) {
    const pdfBlob = createPDF(sheet);
    ui.alert('📥 PDF Export', 'Summary exported as PDF. Check your Google Drive.', ui.ButtonSet.OK);
  }
}

// Function to generate PDF of the summary
function createPDF(sheet) {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const pdfName = `Bill_Summary_${new Date().toISOString().slice(0, 10)}.pdf`;
  
  // Replace this with your actual folder ID
  // For testing, you can use DriveApp.getRootFolder() instead
  let pdfFolder;
  try {
    pdfFolder = DriveApp.getFolderById("YOUR_DRIVE_FOLDER_ID"); // Replace with your folder ID
  } catch (e) {
    // Fallback to root folder if ID is invalid
    pdfFolder = DriveApp.getRootFolder();
    console.log("Using root folder for PDF export. Please update the folder ID.");
  }
  
  const pdfBlob = spreadsheet.getAs(MimeType.PDF);
  pdfFolder.createFile(pdfBlob).setName(pdfName);
  return pdfBlob;
}

// Function to setup the complete sheet structure
function setupCompleteSheet() {
  const ui = SpreadsheetApp.getUi();
  const confirmResponse = ui.alert('Reset Sheet', 'This will clear the entire sheet and set up a new billing structure. Continue?', ui.ButtonSet.YES_NO);
  
  if (confirmResponse !== ui.Button.YES) return;
  
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  sheet.clear();
  
  // Create only one default bill (Bill 1) with the updated standard items
  const structure = [
    ['Item Name', 'HSN / SAC', 'Quantity', 'Rate (INR)', 'SGST %', 'CGST %', 'Amount Without GST', 'SGST Value', 'CGST Value', 'Grand Total'],
    ['BILL 1', '', '', '', '', '', '', '', '', ''],
    ['Item Name', 'HSN / SAC', 'Quantity', 'Rate (INR)', 'SGST %', 'CGST %', 'Amount Without GST', 'SGST Value', 'CGST Value', 'Grand Total'],
    ['Top set', '6206', 100, 20, 2.5, 2.5, '', '', '', ''],
    ['Suit set', '6203', 50, 30, 2.5, 2.5, '', '', '', ''],
    ['Nicker set', '6203', 100, 40, 2.5, 2.5, '', '', '', ''],
    ['Capri set', '6108', 100, 40, 2.5, 2.5, '', '', '', ''],
    ['Mix hosery goods', '6115', 50, 35, 2.5, 2.5, '', '', '', ''],
    ['', '', '', '', '', '', '', '', '', ''],
    ['Total SGST:', '', '', '', '', '', '', '', '', ''],
    ['Total CGST:', '', '', '', '', '', '', '', '', ''],
    ['Total Without GST:', '', '', '', '', '', '', '', '', ''],
    ['Total With GST:', '', '', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', '', '', ''],
    ['GRAND TOTAL (ALL BILLS)', '', '', '', '', '', '', '', '', ''],
    ['All Bills Total SGST:', '', '', '', '', '', '', '', '', ''],
    ['All Bills Total CGST:', '', '', '', '', '', '', '', '', ''],
    ['All Bills Total Without GST:', '', '', '', '', '', '', '', '', ''],
    ['All Bills Total With GST:', '', '', '', '', '', '', '', '', '']
  ];
  
  for (let i = 0; i < structure.length; i++) {
    for (let j = 0; j < structure[i].length; j++) {
      sheet.getRange(i + 1, j + 1).setValue(structure[i][j]);
    }
  }
  
  const headerRange = sheet.getRange(1, 1, 1, 10);
  headerRange.setBackground('#4CAF50').setFontColor('white').setFontWeight('bold');
  
  const bill1Range = sheet.getRange(2, 1, 1, 10);
  bill1Range.setBackground('#4CAF50').setFontColor('white').setFontWeight('bold');
  
  const columnHeaderRange = sheet.getRange(3, 1, 1, 10);
  columnHeaderRange.setBackground('#E8F5E8').setFontWeight('bold');
  
  const grandTotalRange = sheet.getRange(14, 1, 1, 10);
  grandTotalRange.setBackground('#FF9800').setFontColor('white').setFontWeight('bold');
  
  const totalRanges = [
    sheet.getRange(9, 1, 4, 10),
    sheet.getRange(15, 1, 4, 10)
  ];
  
  totalRanges.forEach(range => range.setBackground('#FFF3E0').setFontWeight('bold'));
  
  sheet.autoResizeColumns(1, 10);
  calculateBills();
  ui.alert('✅ Sheet setup completed with calculations!');
}

// Function to add items to existing bill
function addItemToBill() {
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const data = sheet.getDataRange().getValues();
  
  const bills = [];
  for (let i = 0; i < data.length; i++) {
    const cell = (data[i][0]?.toString() || '').toUpperCase();
    if (cell && cell.startsWith("BILL")) {
      bills.push({ name: cell, row: i + 1 });
    }
  }
  
  if (bills.length === 0) {
    ui.alert('❌ No bills found! Please add a bill first.');
    return;
  }
  
  const billNames = bills.map(bill => bill.name).join('\n');
  const billResponse = ui.prompt('Select Bill', `Enter bill name to add item to:\n\n${billNames}\n\nEnter exact bill name:`, ui.ButtonSet.OK_CANCEL);
  
  if (billResponse.getSelectedButton() == ui.Button.CANCEL) return;
  
  const selectedBill = billResponse.getResponseText().trim().toUpperCase();
  const targetBill = bills.find(bill => bill.name === selectedBill);
  
  if (!targetBill) {
    ui.alert('❌ Bill not found! Please enter exact bill name.');
    return;
  }
  
  const itemResponse = ui.prompt('Add Item', 'Enter item details (Format: ItemName,HSN/SAC,Quantity,Rate,SGST%,CGST%)\nExample: top set,1234,2,500,2.5,2.5', ui.ButtonSet.OK_CANCEL);
  
  if (itemResponse.getSelectedButton() == ui.Button.CANCEL) return;
  
  const itemDetails = itemResponse.getResponseText().split(',');
  if (itemDetails.length !== 6) {
    ui.alert('❌ Invalid format! Please use: ItemName,HSN/SAC,Quantity,Rate,SGST%,CGST%');
    return;
  }
  
  // Find where to insert the new item (before the total rows)
  let insertRow = targetBill.row + 2; // Skip bill header and column header
  let foundTotalRow = false;
  
  for (let i = targetBill.row + 2; i < data.length; i++) {
    const cellValue = (data[i][0]?.toString() || '').toUpperCase();
    if (cellValue === "TOTAL SGST:" || cellValue.startsWith("BILL") || cellValue.includes("GRAND TOTAL")) {
      insertRow = i + 1;
      foundTotalRow = true;
      break;
    }
  }
  
  // If we didn't find a total row, add one before inserting the item
  if (!foundTotalRow) {
    // Add empty row before totals
    sheet.insertRowBefore(insertRow);
    sheet.getRange(insertRow, 1, 1, 10).setValue(['', '', '', '', '', '', '', '', '', '']);
    insertRow++;
    
    // Add total rows
    const totalRows = [
      ['Total SGST:', '', '', '', '', '', '', '', '', ''],
      ['Total CGST:', '', '', '', '', '', '', '', '', ''],
      ['Total Without GST:', '', '', '', '', '', '', '', '', ''],
      ['Total With GST:', '', '', '', '', '', '', '', '', '']
    ];
    
    for (const row of totalRows) {
      sheet.insertRowBefore(insertRow);
      sheet.getRange(insertRow, 1, 1, 10).setValues([row]);
      sheet.getRange(insertRow, 1, 1, 10).setBackground('#FFF3E0').setFontWeight('bold');
      insertRow++;
    }
    
    // Add empty row after totals
    sheet.insertRowBefore(insertRow);
    sheet.getRange(insertRow, 1, 1, 10).setValue(['', '', '', '', '', '', '', '', '', '']);
    
    // Reset insert position for the new item
    insertRow = targetBill.row + 2;
  }
  
  // Insert the new item
  sheet.insertRowBefore(insertRow);
  sheet.getRange(insertRow, 1).setValue(itemDetails[0].trim());
  sheet.getRange(insertRow, 2).setValue(itemDetails[1].trim());
  sheet.getRange(insertRow, 3).setValue(parseFloat(itemDetails[2]) || 0);
  sheet.getRange(insertRow, 4).setValue(parseFloat(itemDetails[3]) || 0);
  sheet.getRange(insertRow, 5).setValue(parseFloat(itemDetails[4]) || 0);
  sheet.getRange(insertRow, 6).setValue(parseFloat(itemDetails[5]) || 0);
  
  calculateBills();
  ui.alert(`✅ Item "${itemDetails[0]}" added to ${selectedBill} successfully!`);
}

// Function to increase items in a bill
function increaseItemsInBill() {
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const data = sheet.getDataRange().getValues();
  
  // Find all bills
  const bills = [];
  for (let i = 0; i < data.length; i++) {
    const cell = (data[i][0]?.toString() || '').toUpperCase();
    if (cell && cell.startsWith("BILL")) {
      bills.push({ name: cell, row: i + 1 });
    }
  }
  
  if (bills.length === 0) {
    ui.alert('❌ No bills found! Please add a bill first.');
    return;
  }
  
  // Prompt user to select a bill
  const billNames = bills.map(bill => bill.name).join('\n');
  const billResponse = ui.prompt('Select Bill', `Enter bill name to add items to:\n\n${billNames}\n\nEnter exact bill name:`, ui.ButtonSet.OK_CANCEL);
  
  if (billResponse.getSelectedButton() == ui.Button.CANCEL) return;
  
  const selectedBill = billResponse.getResponseText().trim().toUpperCase();
  const targetBill = bills.find(bill => bill.name === selectedBill);
  
  if (!targetBill) {
    ui.alert('❌ Bill not found! Please enter exact bill name.');
    return;
  }
  
  // Prompt for number of items to add
  const countResponse = ui.prompt('Add Items', 'How many items do you want to add?', ui.ButtonSet.OK_CANCEL);
  
  if (countResponse.getSelectedButton() == ui.Button.CANCEL) return;
  
  const itemCount = parseInt(countResponse.getResponseText().trim());
  if (isNaN(itemCount) || itemCount <= 0) {
    ui.alert('❌ Please enter a valid positive number.');
    return;
  }
  
  // Find where to insert the new items (before the total rows)
  let insertRow = targetBill.row + 2; // Skip bill header and column header
  let totalRowIndex = -1;
  
  for (let i = targetBill.row + 2; i < data.length; i++) {
    const cellValue = (data[i][0]?.toString() || '').toUpperCase();
    if (cellValue === "TOTAL SGST:" || cellValue.startsWith("BILL") || cellValue.includes("GRAND TOTAL")) {
      totalRowIndex = i;
      insertRow = i;
      break;
    }
    
    // If we reach the end of the data, set the insert row to the last row
    if (i === data.length - 1) {
      insertRow = i + 1;
    }
  }
  
  // Add the new items
  for (let i = 0; i < itemCount; i++) {
    sheet.insertRowBefore(insertRow);
    sheet.getRange(insertRow, 1).setValue(`Item ${i+1}`);
    sheet.getRange(insertRow, 2).setValue('');
    sheet.getRange(insertRow, 3).setValue(1);
    sheet.getRange(insertRow, 4).setValue(100);
    sheet.getRange(insertRow, 5).setValue(2.5);
    sheet.getRange(insertRow, 6).setValue(2.5);
  }
  
  calculateBills();
  ui.alert(`✅ Added ${itemCount} items to ${selectedBill} successfully!`);
}

// Function to decrease items in a bill
function decreaseItemsInBill() {
  const ui = SpreadsheetApp.getUi();
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const data = sheet.getDataRange().getValues();
  
  // Find all bills
  const bills = [];
  for (let i = 0; i < data.length; i++) {
    const cell = (data[i][0]?.toString() || '').toUpperCase();
    if (cell && cell.startsWith("BILL")) {
      bills.push({ name: cell, row: i + 1 });
    }
  }
  
  if (bills.length === 0) {
    ui.alert('❌ No bills found!');
    return;
  }
  
  // Prompt user to select a bill
  const billNames = bills.map(bill => bill.name).join('\n');
  const billResponse = ui.prompt('Select Bill', `Enter bill name to remove items from:\n\n${billNames}\n\nEnter exact bill name:`, ui.ButtonSet.OK_CANCEL);
  
  if (billResponse.getSelectedButton() == ui.Button.CANCEL) return;
  
  const selectedBill = billResponse.getResponseText().trim().toUpperCase();
  const targetBill = bills.find(bill => bill.name === selectedBill);
  
  if (!targetBill) {
    ui.alert('❌ Bill not found! Please enter exact bill name.');
    return;
  }
  
  // Count items in the bill
  let itemCount = 0;
  let startRow = targetBill.row + 2; // Skip bill header and column header
  let totalRowIndex = -1;
  
  for (let i = startRow; i < data.length; i++) {
    const cellValue = (data[i][0]?.toString() || '').toUpperCase();
    if (cellValue === "TOTAL SGST:" || cellValue.startsWith("BILL") || cellValue.includes("GRAND TOTAL") || cellValue === "") {
      totalRowIndex = i;
      break;
    }
    itemCount++;
  }
  
  if (itemCount === 0) {
    ui.alert('❌ No items found in this bill!');
    return;
  }
  
  // Prompt for number of items to remove
  const countResponse = ui.prompt('Remove Items', `This bill has ${itemCount} items. How many items do you want to remove?`, ui.ButtonSet.OK_CANCEL);
  
  if (countResponse.getSelectedButton() == ui.Button.CANCEL) return;
  
  const removeCount = parseInt(countResponse.getResponseText().trim());
  if (isNaN(removeCount) || removeCount <= 0) {
    ui.alert('❌ Please enter a valid positive number.');
    return;
  }
  
  if (removeCount >= itemCount) {
    ui.alert('⚠️ Cannot remove all items. At least one item must remain in the bill.');
    return;
  }
  
  // Remove the items from the end
  sheet.deleteRows(totalRowIndex - removeCount, removeCount);
  
  calculateBills();
  ui.alert(`✅ Removed ${removeCount} items from ${selectedBill} successfully!`);
}

// Helper function to check if a row is within a bill section
function isInBillSection(data, row) {
  // Check rows above until we find a bill header
  let foundBill = false;
  for (let i = row - 2; i >= 0; i--) {
    if (!data[i]) continue;
    const cellValue = (data[i][0]?.toString() || '').trim().toUpperCase();
    if (cellValue.startsWith("BILL")) {
      foundBill = true;
      break;
    }
    if (cellValue.includes("GRAND TOTAL")) {
      return false;
    }
  }
  return foundBill;
}

// Function to create professional menu
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('💼 Professional Billing')
    .addItem('📊 Recalculate Bills', 'calculateBills')
    .addItem('🔄 Recalculate After Row Deletion', 'recalculateAfterRowDeletion')
    .addSeparator()
    .addItem('➕ Add New Bill', 'addNewBill')
    .addItem('🔄 Add Multiple Bills', 'addMultipleBills')
    .addItem('🔧 Add Item to Bill', 'addItemToBill')
    .addItem('➕ Increase Items in Bill', 'increaseItemsInBill')
    .addItem('➖ Decrease Items in Bill', 'decreaseItemsInBill')
    .addItem('✏️ Edit Item', 'editItem')
    .addSeparator()
    .addItem('🗑️ Delete Bill', 'deleteBill')
    .addItem('🗑️ Delete Selected Rows', 'deleteSelectedRowsAndRecalculate')
    .addSeparator()
    .addItem('📈 View Summary & Export', 'showBillSummary')
    .addItem('🔄 Reset & Setup', 'setupCompleteSheet')
    .addToUi();
}

// Function for menu to add a new bill
function addNewBill() {
  addNewBillAdvanced();
}

// Function to recalculate after row deletion
function recalculateAfterRowDeletion() {
  calculateBills();
  SpreadsheetApp.getUi().alert('✅ Bills recalculated successfully after row deletion!');
}

// Function to manually delete rows and recalculate
function deleteSelectedRowsAndRecalculate() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const selectedRange = sheet.getActiveRange();
  const ui = SpreadsheetApp.getUi();
  
  if (!selectedRange) {
    ui.alert('❌ Please select the row(s) you want to delete first.');
    return;
  }
  
  const startRow = selectedRange.getRow();
  const numRows = selectedRange.getNumRows();
  
  // Check if user is trying to delete a bill header or total row
  const data = sheet.getRange(startRow, 1, numRows, 1).getValues();
  const criticalRows = data.filter(row => {
    const cellValue = (row[0]?.toString() || '').trim().toUpperCase();
    return cellValue.startsWith("BILL") || 
           cellValue === "TOTAL SGST:" || 
           cellValue === "TOTAL CGST:" || 
           cellValue === "TOTAL WITHOUT GST:" || 
           cellValue === "TOTAL WITH GST:" ||
           cellValue.includes("GRAND TOTAL");
  });
  
  if (criticalRows.length > 0) {
    const confirmDelete = ui.alert(
      '⚠️ Warning: Critical Rows Selected', 
      'You are about to delete bill headers or total rows. This may break calculations.\n\nTo delete an entire bill, use the "Delete Bill" menu option instead.\n\nDo you still want to proceed?', 
      ui.ButtonSet.YES_NO
    );
    
    if (confirmDelete !== ui.Button.YES) {
      return;
    }
  } else {
    // Normal confirmation
    const confirmDelete = ui.alert(
      'Confirm Deletion', 
      `Are you sure you want to delete ${numRows} row(s)?\nThis action cannot be undone.`, 
      ui.ButtonSet.YES_NO
    );
    
    if (confirmDelete !== ui.Button.YES) {
      return;
    }
  }
  
  try {
    // Delete the selected rows
    sheet.deleteRows(startRow, numRows);
    
    // Recalculate bills
    calculateBills();
    
    ui.alert(`✅ Successfully deleted ${numRows} row(s) and recalculated bills.`);
  } catch (error) {
    ui.alert(`❌ Error deleting rows: ${error.message}`);
    console.error(`Error in deleteSelectedRowsAndRecalculate: ${error.message}`);
  }
}

// Function to add multiple bills at once
function addMultipleBills() {
  const ui = SpreadsheetApp.getUi();
  
  // First, ask how many bills to add
  const countResponse = ui.prompt(
    '🔢 Add Multiple Bills',
    'How many bills would you like to add? (1-20)',
    ui.ButtonSet.OK_CANCEL
  );
  
  if (countResponse.getSelectedButton() !== ui.Button.OK) {
    return;
  }
  
  const billCount = parseInt(countResponse.getResponseText().trim());
  if (isNaN(billCount) || billCount < 1 || billCount > 20) {
    ui.alert('❌ Please enter a valid number between 1 and 20.');
    return;
  }
  
  // Ask for bill template configuration
  const templateResponse = ui.prompt(
    '📋 Bill Template Configuration',
    'Would you like to configure the default items for all bills?\n\n' +
    'Enter Y to customize or N to use default items.\n\n' +
    'Default items: Top set, Suit set, Nicker set, Capri set, Mix hosery goods',
    ui.ButtonSet.YES_NO_CANCEL
  );
  
  if (templateResponse.getSelectedButton() === ui.Button.CANCEL) {
    return;
  }
  
  let customItems = [];
  
  if (templateResponse.getSelectedButton() === ui.Button.YES) {
    // Ask for custom items
    const itemsResponse = ui.prompt(
      '📝 Custom Items',
      'Enter custom items in the format:\n' +
      'Item1,HSN1,Qty1,Rate1,SGST1,CGST1|Item2,HSN2,Qty2,Rate2,SGST2,CGST2|...\n\n' +
      'Example: Top set,6206,10,100,2.5,2.5|Suit set,6203,5,200,2.5,2.5\n\n' +
      'Leave blank to use default items.',
      ui.ButtonSet.OK_CANCEL
    );
    
    if (itemsResponse.getSelectedButton() === ui.Button.CANCEL) {
      return;
    }
    
    const itemsText = itemsResponse.getResponseText().trim();
    
    if (itemsText) {
      try {
        // Parse custom items
        const itemGroups = itemsText.split('|');
        
        for (const group of itemGroups) {
          const parts = group.split(',');
          if (parts.length >= 6) {
            customItems.push({
              name: parts[0].trim(),
              hsn: parts[1].trim(),
              qty: parseFloat(parts[2]) || 1,
              rate: parseFloat(parts[3]) || 0,
              sgst: parseFloat(parts[4]) || 2.5,
              cgst: parseFloat(parts[5]) || 2.5
            });
          }
        }
        
        if (customItems.length === 0) {
          ui.alert('⚠️ No valid custom items found. Using default items.');
          customItems = [];
        }
      } catch (e) {
        ui.alert('❌ Error parsing custom items. Using default items.');
        console.error('Error parsing custom items:', e);
        customItems = [];
      }
    }
  }
  
  // Ask for starting bill number
  const startResponse = ui.prompt(
    '🔢 Starting Bill Number',
    'Enter the starting bill number:',
    ui.ButtonSet.OK_CANCEL
  );
  
  if (startResponse.getSelectedButton() !== ui.Button.OK) {
    return;
  }
  
  let startNumber = parseInt(startResponse.getResponseText().trim());
  if (isNaN(startNumber) || startNumber < 1) {
    startNumber = findNextBillNumber([]);
  }
  
  // Confirm before adding bills
  const confirmResponse = ui.alert(
    '✅ Confirm',
    `You are about to add ${billCount} bills starting from BILL ${startNumber}.\n\n` +
    `${customItems.length > 0 ? 'Using ' + customItems.length + ' custom items.' : 'Using default items.'}\n\n` +
    'Do you want to proceed?',
    ui.ButtonSet.YES_NO
  );
  
  if (confirmResponse !== ui.Button.YES) {
    return;
  }
  
  // Start adding bills
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const data = sheet.getDataRange().getValues();
  
  // Find where to insert the bills
  let insertRow = data.length + 1;
  
  // Check for grand total row
  for (let i = 0; i < data.length; i++) {
    if ((data[i][0]?.toString() || '').toUpperCase().includes("GRAND TOTAL")) {
      insertRow = i + 1;
      break;
    }
  }
  
  // Add each bill
  let addedBills = 0;
  
  try {
    for (let i = 0; i < billCount; i++) {
      const billName = `BILL ${startNumber + i}`;
      
      // Create bill template
      const billTemplate = createBillTemplate(billName, customItems);
      
      // Insert rows for the bill template in reverse order
      for (let j = billTemplate.length - 1; j >= 0; j--) {
        sheet.insertRowBefore(insertRow);
        const row = billTemplate[j];
        for (let k = 0; k < row.length; k++) {
          sheet.getRange(insertRow, k + 1).setValue(row[k] || '');
        }
      }
      
      // Apply formatting
      const headerRange = sheet.getRange(insertRow, 1, 1, 10);
      headerRange.setBackground('#4CAF50').setFontColor('white').setFontWeight('bold');
      
      const columnHeaderRange = sheet.getRange(insertRow + 1, 1, 1, 10);
      columnHeaderRange.setBackground('#E8F5E8').setFontWeight('bold');
      
      const totalRowsCount = 4; // SGST, CGST, Without GST, With GST
      const itemCount = customItems.length > 0 ? customItems.length : 5; // Default is 5 items
      const totalRowStartIndex = insertRow + 2 + itemCount + 1; // +1 for empty row before totals
      
      const totalRange = sheet.getRange(totalRowStartIndex, 1, totalRowsCount, 10);
      totalRange.setBackground('#FFF3E0').setFontWeight('bold');
      
      // Move insertion point past this bill for next iteration
      insertRow += billTemplate.length;
      
      addedBills++;
    }
    
    // Recalculate all bills
    calculateBills();
    
    ui.alert(`✅ Successfully added ${addedBills} bills!`);
  } catch (e) {
    ui.alert(`❌ Error adding bills: ${e.message}\n\nSuccessfully added ${addedBills} bills before the error.`);
    console.error('Error in addMultipleBills:', e);
  }
}

// Helper function to create bill template with custom items
function createBillTemplate(billName, customItems) {
  // Start with bill header and column header
  const template = [
    [billName, '', '', '', '', '', '', '', '', ''],
    ['Item Name', 'HSN / SAC', 'Quantity', 'Rate (INR)', 'SGST %', 'CGST %', 'Amount Without GST', 'SGST Value', 'CGST Value', 'Grand Total']
  ];
  
  // Add items
  if (customItems && customItems.length > 0) {
    // Use custom items
    for (const item of customItems) {
      template.push([
        item.name,
        item.hsn,
        item.qty,
        item.rate,
        item.sgst,
        item.cgst,
        '', '', '', ''
      ]);
    }
  } else {
    // Use default items
    template.push(
      ['Top set', '6206', 1, 0, 2.5, 2.5, '', '', '', ''],
      ['Suit set', '6203', 1, 0, 2.5, 2.5, '', '', '', ''],
      ['Nicker set', '6203', 1, 0, 2.5, 2.5, '', '', '', ''],
      ['Capri set', '6108', 1, 0, 2.5, 2.5, '', '', '', ''],
      ['Mix hosery goods', '6115', 1, 0, 2.5, 2.5, '', '', '', '']
    );
  }
  
  // Add empty row before totals
  template.push(['', '', '', '', '', '', '', '', '', '']);
  
  // Add total rows
  template.push(
    ['Total SGST:', '', '', '', '', '', '', '', '', ''],
    ['Total CGST:', '', '', '', '', '', '', '', '', ''],
    ['Total Without GST:', '', '', '', '', '', '', '', '', ''],
    ['Total With GST:', '', '', '', '', '', '', '', '', '']
  );
  
  // Add empty row after totals
  template.push(['', '', '', '', '', '', '', '', '', '']);
  
  return template;
} 
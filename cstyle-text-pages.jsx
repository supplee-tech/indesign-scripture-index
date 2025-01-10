#target "InDesign"

// Function to get all character styles in the document
function getAllCharacterStyles(doc) {
	return doc.characterStyles.everyItem().name;
}

function trim(str) {
    return str.replace(/^\s+|\s+$/g, '');
}

function getFootnoteNumber(item) {
	var noteNumber = null;

	var parent = item.parent;
	while (parent) {
		if (parent.constructor.name === "Footnote") {
			var story = parent.storyOffset.parent;
			noteNumber = 0;
			for (var j = 0; j < story.footnotes.length; j++) {
				if (story.footnotes[j] === parent) {
					noteNumber = j + 1; // Footnote index is 0-based
					break;
				}
			}
			break;
		}
		if (parent.parent == parent) {
			break;
		}
		parent = parent.parent;
	}

	return noteNumber
}

// Function to get text by character style (optimized)
function getTextByCharacterStyle(doc, characterStyleName, inNote) {
	var results = [];
	var characterStyle = doc.characterStyles.itemByName(characterStyleName);

    app.findTextPreferences = app.changeTextPreferences = null;
    app.findTextPreferences.appliedCharacterStyle = characterStyle;
    app.findChangeTextOptions.includeFootnotes = inNote;

    // app.findChangeTextOptions.includeFootnotes = inNote;
	// app.findTextPreferences = app.changeTextPreferences = null;
	// app.findTextPreferences.appliedCharacterStyle = characterStyle;

	var foundItems = doc.findText();

	for (var i = 0; i < foundItems.length; i++) {
		var foundItem = foundItems[i];
		var pageNumber = null;

		try {
        	pageNumber = foundItem.parentTextFrames[0].parentPage.name;
		} catch (error) {
			// do nothing
        }
		results.push({
			text: trim(foundItem.contents),
			page: pageNumber,
			noteNumber: getFootnoteNumber(foundItem),
		});
	}

	app.findTextPreferences = app.changeTextPreferences = null;
	return results;
}

// Function to get all condition names in the document
function getAllConditionNames(doc) {
    return ['[None]'].concat(doc.conditions.everyItem().name);
    // return doc.conditions.everyItem().name;
}

function getHiddenConditionalText(doc, conditionName) {
    var results = [];
    var condition = doc.conditions.itemByName(conditionName);
	var hiddenTexts = doc.stories.everyItem().hiddenTexts.everyItem().getElements();

	for (i = 0; i < hiddenTexts.length; i++) {
		var hiddenText = hiddenTexts[i];
		if (hiddenText.texts[0].appliedConditions[0].name === conditionName) {
		    results.push({
				text: trim(hiddenText.texts[0].contents),
				page: hiddenText.storyOffset.parentTextFrames[0].parentPage.name,
				noteNumber: getFootnoteNumber(hiddenText.storyOffset)
			});
		}
	}

	return results;
}

// Function to get text by condition name (optimized)
function getTextByCondition(doc, conditionName) {
    var results = [];
    var condition = doc.conditions.itemByName(conditionName);

    app.findChangeTextOptions.includeFootnotes = true;
    app.findChangeTextOptions.includeHiddenLayers = true;
    app.findChangeTextOptions.includeLockedLayersForFind = true;
    app.findChangeTextOptions.includeLockedStoriesForFind = true;
    app.findChangeTextOptions.includeMasterPages = true;

    app.findTextPreferences = app.changeTextPreferences = null;
	// app.findTextPreferences.appliedCharacterStyle = null;
    app.findTextPreferences.appliedConditions = [condition];
    // app.findTextPreferences.hiddenText = true;

    var foundItems = doc.findText();

    for (var i = 0; i < foundItems.length; i++) {
        var foundItem = foundItems[i];
        var text = foundItem.contents;
		var pageNumber = null
		try {
        	pageNumber = foundItem.parentTextFrames[0].parentPage.name;
		} catch (error) {
			// do nothing
		}
        results.push({text: trim(text), page: pageNumber});
    }

    app.findTextPreferences = app.changeTextPreferences = null;
    return results;
}

function getComments(doc) {
    var results = [];

	alert("Processing notes...");
    // Process all stories in the document
    for (var i = 0; i < doc.stories.length; i++) {
		var story = doc.stories[i];
        for (var j = 0; j < story.notes.length; j++) {
            var note = story.notes[j];
            var noteText = note.texts[0].contents;
			var pageNumber = null;
			try {
				pageNumber = note.insertionPoints[0].parentTextFrames[0].parentPage.name;
			} catch (e) {
				// do nothing
			}
			// if (note.insertionPoints && note.insertionPoints.length > 0 && note.insertionPoints[0] && note.insertionPoints[0].parentTextFrames && note.insertionPoints[0].parentTextFrames.length > 0 && note.insertionPoints[0].parentTextFrames[0].parentPage) {
			// 	pageNumber = note.insertionPoints[0].parentTextFrames[0].parentPage.name;
			// }
			results.push({text: noteText, page: pageNumber});
        }
    }

    return results;
}

// Function to write results to a file
function writeResultsToFile(results, filePath) {
	var file = new File(filePath);
	file.encoding = "UTF-8";
	file.open("w");

	file.writeln('text,page,note_num');

	for (var i = 0; i < results.length; i++) {
		file.writeln('"' + results[i].text + '", ' + results[i].page + ', ' + (results[i].noteNumber ? results[i].noteNumber : ""));
	}

	file.close();
}

// Main script
// try {
	var doc = app.activeDocument;

	// Get all character styles
	var characterStyles = getAllCharacterStyles(doc);

	// Get all condition names
	var conditionNames = getAllConditionNames(doc);

	// Create a dialog for style selection
	var dialog = new Window("dialog", "Character Style Page Data");
	dialog.orientation = "column";
	dialog.alignChildren = ["left", "top"];

    dialog.add("statictext", undefined, "Select a Character Style:");
	var dropdown = dialog.add("dropdownlist", undefined, characterStyles);
	dropdown.selection = 0;

    dialog.add("statictext", undefined, "Select a Conditional Text:");
    var conditionDropdown = dialog.add("dropdownlist", undefined, conditionNames);
    conditionDropdown.selection = 0;

	var btnGroup = dialog.add("group");
	btnGroup.orientation = "row";
	var okButton = btnGroup.add("button", undefined, "OK");
	var cancelButton = btnGroup.add("button", undefined, "Cancel");

	var selectedStyle = null;
	var selectedCondition = null;

	okButton.onClick = function() {
		selectedStyle = dropdown.selection.text;
		selectedCondition = conditionDropdown.selection.text;
		dialog.close();
	}

	cancelButton.onClick = function() {
		dialog.close();
	}

	dialog.show();

	var results = [];

	if (selectedStyle && selectedStyle !== "[None]") {
		results = results.concat(getTextByCharacterStyle(doc, selectedStyle, true));
	}
	if (selectedCondition && selectedCondition!== "[None]") {
		results = results.concat(getHiddenConditionalText(doc, selectedCondition));
	}

	// results = results.concat(getComments(doc));

	if (results.length > 0) {
		// Prompt for save location
		var saveFile = File.saveDialog("Save results as", "*.csv");

		if (saveFile) {
			writeResultsToFile(results, saveFile.fsName);
			alert("Results have been saved to:\n" + saveFile.fsName);
		} else {
			// alert("Save operation cancelled.");
		}
	} else {
		alert("No text found.");
	}

// } catch (error) {
// 	alert("An error occurred: " + error);
// }
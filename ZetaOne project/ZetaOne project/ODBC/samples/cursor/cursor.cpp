/*
Copyright (c) 2003-2004  Sybase, Inc.

Module Name:
	cursor.cpp

Abstract:
 	Sample ODBC console application.
 	Sample for update cursor and delete cursor

*/


#if defined (WIN32) || defined(_WIN32)
#include <windows.h>
#else
#include <stdlib.h>
#include <stddef.h>
#endif
#include <string.h>
#include <sql.h>
#include <sqlext.h>
#include <iostream>
#ifdef  LINUX
#ifndef SQLLEN
#define SQLLEN SQLINTEGER
#endif
#ifndef SQLULEN
#define SQLULEN SQLUINTEGER
#endif
#endif
#ifndef _ODBCSTRTYPE
#if defined(UNICODE) || defined(_UNICODE)
#define _ODBCSTRTYPE(str)		(SQLWCHAR *)L##str
#else
#define _ODBCSTRTYPE(str)		(SQLCHAR *)str
#endif
#endif
#ifndef TCOUT
#if defined(UNICODE) || defined(_UNICODE)
#define TCOUT		wcout
#else
#define TCOUT		cout
#endif
#endif
#ifndef TCIN
#if defined(UNICODE) || defined(_UNICODE)
#define TCIN(str,len)		wcin.getline((wchar_t*)str, len)
#else
#define TCIN(str,len)		cin.getline((char*)str, len)
#endif
#endif

void executeStatement(SQLHSTMT, SQLTCHAR*);
void finish(SQLHENV , SQLHDBC , SQLHSTMT, bool);
void sqlok(SQLHSTMT stmt, SQLRETURN retcode, char* message);

using namespace std;

#define STMT_LEN 255
#define NAME_LEN 21
#define ERR_MSG_LEN	255

#if defined(WIN32) && defined(UNICODE)
int wmain(int argc, wchar_t* argv[])
#else
int main(int argc, char* argv[])
#endif
{
	SQLHENV	env	= SQL_NULL_HANDLE;
	SQLHDBC	dbc = SQL_NULL_HANDLE;
	SQLHSTMT 	stmt = SQL_NULL_HANDLE, stmtcur	= SQL_NULL_HANDLE;
	SQLTCHAR	connString[512];
	SQLRETURN retcode ;
	SQLLEN fNameLen = 0;
	SQLLEN lNameLen = 0;
	SQLINTEGER empID = 0;
	SQLCHAR lName[ NAME_LEN ];
	SQLSMALLINT curNameLen = 0;
	SQLTCHAR curName[NAME_LEN];
	SQLTCHAR* droptable = _ODBCSTRTYPE("drop table t_CursorTable");
	SQLTCHAR* createtable = _ODBCSTRTYPE("Create table t_CursorTable ( EmpID int null, FirstName varchar(20) null, LastName varchar(20) null)");
	SQLTCHAR* uniqueconstraint = _ODBCSTRTYPE("create unique index emp_unique  on t_CursorTable (EmpID ) ");
	SQLTCHAR* insertstmt = _ODBCSTRTYPE("Insert into t_CursorTable values (1,'John', 'Smith')");
	SQLTCHAR* selectstmt = _ODBCSTRTYPE("select EmpID, LastName from t_CursorTable");
	SQLTCHAR* selectstmt2 = _ODBCSTRTYPE("select LastName from t_CursorTable ");
	SQLTCHAR* updatestmt = _ODBCSTRTYPE("Update t_CursorTable set LastName='UpdateLastName' where current of CustUpdate");
	SQLTCHAR* cursorName = _ODBCSTRTYPE("CustUpdate");
	SQLTCHAR* deletestmt = _ODBCSTRTYPE("delete from t_CursorTable where current of CustUpdate");
	int lengthOfDefault = strlen("DSN=sampledsn");
	retcode = SQLAllocHandle(SQL_HANDLE_ENV, SQL_NULL_HANDLE, &env);

	if (retcode != SQL_SUCCESS && retcode != SQL_SUCCESS_WITH_INFO)
	{
		cout << "Allocating Environment Handle failed; SQLRETURN code is :" << retcode ;
		exit(1);
	}

	/* Set the ODBC version environment attribute */
	SQLSetEnvAttr(env, SQL_ATTR_ODBC_VERSION, (void*)SQL_OV_ODBC3, 0);

	retcode = SQLAllocHandle(SQL_HANDLE_DBC, env, &dbc);
	sqlok(stmt, retcode, (char *)"Allocating connection handle failed");

	if(argc == 4)
	{
#if defined(UNICODE)
#if defined(WIN32)
		wstring tmpConnString = wstring(L"DSN=");
		tmpConnString += wstring(argv[1]);
		tmpConnString += wstring(L";UID=");
		tmpConnString += wstring(argv[2]);
		tmpConnString += wstring(L";PWD=");
		tmpConnString += wstring(argv[3]);
		wcout << L"Using connection string \"" << tmpConnString.c_str() << L"\"" << endl;
		memcpy(connString, tmpConnString.c_str(), tmpConnString.length()*sizeof(SQLTCHAR));
		connString[tmpConnString.length()] = 0;
#else
		//The connection string is hard coded because wmain is non-standared c++
		//A complete string converter, which is not in the scope of this sample, would be required for command line input
		//NOTE we are only able to build with UNICODE defined on platforms that allow the
		//redefinition of wchar_t from 32bit to 16bit to match SQLWCHAR
		cout << "Using connection string \"DSN=sampledsn\"" << endl;
		memcpy(connString, _ODBCSTRTYPE("DSN=sampledsn"), lengthOfDefault*sizeof(SQLTCHAR));
		connString[lengthOfDefault] = 0;
#endif
#else
		string tmpConnString = string("DSN=");
		tmpConnString += string(argv[1]);
		tmpConnString += string(";UID=");
		tmpConnString += string(argv[2]);
		tmpConnString += string(";PWD=");
		tmpConnString += string(argv[3]);
		cout << "Using connection string \"" << tmpConnString.c_str() << "\"" << endl;
		memcpy(connString, tmpConnString.c_str(), tmpConnString.length()*sizeof(SQLTCHAR));
		connString[tmpConnString.length()] = 0;
#endif
	}
	else
	{
		cout << "Using connection string \"DSN=sampledsn\"" << endl;
		memcpy(connString, _ODBCSTRTYPE("DSN=sampledsn"), lengthOfDefault*sizeof(SQLTCHAR));
		connString[lengthOfDefault] = 0;
	}
	retcode = SQLDriverConnect(dbc, SQL_NULL_HANDLE, connString, SQL_NTS, SQL_NULL_HANDLE, 0, SQL_NULL_HANDLE, SQL_DRIVER_NOPROMPT);
	sqlok(stmt, retcode, (char *)"Obtaining a connection failed");

	retcode = SQLAllocHandle(SQL_HANDLE_STMT, dbc, &stmt);
	sqlok(stmt, retcode, (char *)"Obtaining statement handle failed");
	retcode = SQLAllocHandle(SQL_HANDLE_STMT, dbc, &stmtcur);
	sqlok(stmt, retcode, (char *)"Obtaining statement handle failed");
	SQLExecDirect(stmt, droptable, SQL_NTS);
	executeStatement(stmt, createtable);
	//create a unique constraint
	executeStatement(stmt, uniqueconstraint);
	//insert a row
	executeStatement(stmt, insertstmt);
	SQLFreeStmt(stmt, SQL_CLOSE);
	executeStatement(stmtcur, selectstmt2);
	retcode = SQLBindCol(stmtcur, 1, SQL_C_CHAR, lName, sizeof(lName), &lNameLen);
	sqlok(stmt, retcode, (char *)"SQLBindCol failed");
	retcode = SQLFetch(stmtcur);
	sqlok(stmt, retcode, (char *)"SQLFetch failed");

	cout << "Inserted Last Name is : " << lName << endl;
	retcode = SQLFreeStmt(stmtcur, SQL_CLOSE);
	cout << " ---- Update sample -----" << endl ;
	//set statement attribute for an updateable cursor
	retcode = SQLSetStmtAttr(stmt, SQL_ATTR_CONCURRENCY, (SQLPOINTER)SQL_CONCUR_LOCK, 0);
	sqlok(stmt, retcode, (char *)"SQLSetStmtAttr failed");
	retcode = SQLSetCursorName(stmt, cursorName , SQL_NTS);
	sqlok(stmt, retcode, (char *)"SQLSetCursorName failed");
	executeStatement(stmt, selectstmt);
	retcode = SQLFetch(stmt);
	sqlok(stmt, retcode, (char *)"SQLFetch failed");
	retcode = SQLGetCursorName(stmt, curName, sizeof(curName), &curNameLen);
	sqlok(stmt, retcode, (char *)"SQLGetCursorName failed");
	cout << "Cursor Name retrieved is ";
	TCOUT << curName;
	cout << endl;
	executeStatement(stmtcur, updatestmt);
	SQLCloseCursor(stmt);
	SQLFreeStmt(stmtcur, SQL_CLOSE);
	executeStatement(stmtcur, selectstmt2);
	retcode = SQLFetch(stmtcur);
	sqlok(stmt, retcode, (char *)"SQLFetch failed");

	cout << "Updated Last Name is " << lName << endl;
	retcode = SQLFreeStmt(stmtcur, SQL_CLOSE);
	//delete
	cout << " ---- Delete sample -----" << endl ;
	retcode = SQLSetStmtAttr(stmt, SQL_ATTR_CONCURRENCY, (SQLPOINTER)SQL_CONCUR_LOCK, 0);
	retcode = SQLSetCursorName(stmt, cursorName , SQL_NTS);
	executeStatement(stmt, selectstmt);
	retcode = SQLFetch(stmt);
	retcode = SQLGetCursorName(stmt, curName, sizeof(curName), &curNameLen);
	cout << "Cursor Name retrieved is ";
	TCOUT << curName;
	cout << endl ;
	executeStatement(stmtcur, deletestmt);
	retcode = SQLCloseCursor(stmt);
	retcode = SQLFreeStmt(stmtcur, SQL_CLOSE);
	executeStatement(stmtcur, selectstmt2);
	retcode = SQLFetch(stmtcur);
	sqlok(stmt, retcode, (char *)"SQLFetch failed");

	SQLFreeStmt(stmtcur, SQL_CLOSE);
	executeStatement(stmt, droptable);
	finish(env , dbc, stmt, false);
	return 0;
}



/**
**	executeStatement
**
**	Executes a sql statement
**/
void executeStatement(SQLHSTMT stmt, SQLTCHAR* statement)
{
	SQLRETURN retcode;
	SQLTCHAR 	errormsg[ERR_MSG_LEN];
	SQLTCHAR	sqlstate[SQL_SQLSTATE_SIZE+1];
	SQLINTEGER	nativeerror = 0;
	SQLSMALLINT errormsglen = 0;
	retcode = SQLExecDirect(stmt, statement, SQL_NTS) ;

	if (retcode != SQL_SUCCESS && retcode != SQL_SUCCESS_WITH_INFO)
	{
		cout << "Executing Statement : ";
		TCOUT << statement;
		cout << " failed SQLRETURN code is " << retcode  << endl;

		if (retcode == SQL_ERROR)
		{
			retcode = SQLGetDiagRec(SQL_HANDLE_STMT, stmt, 1, sqlstate, &nativeerror, errormsg, ERR_MSG_LEN, &errormsglen);

			if (retcode == SQL_SUCCESS || retcode == SQL_SUCCESS_WITH_INFO)
			{
				cout << " SqlState : ";
				TCOUT << sqlstate;
				cout << " Error Message :";
				TCOUT << errormsg;
				cout << endl ;
			}
		}

		exit(1);
	}
}

void finish(SQLHENV env, SQLHDBC dbc, SQLHSTMT stmt, bool doExit)
{
	if (stmt != SQL_NULL_HANDLE)
	{
		SQLFreeStmt(stmt, SQL_CLOSE); //close the result set
		SQLFreeHandle(SQL_HANDLE_STMT, stmt);
	}

	if (dbc != SQL_NULL_HANDLE)
	{
		SQLDisconnect(dbc);
		SQLFreeHandle(SQL_HANDLE_DBC, dbc);
	}

	if (env != SQL_NULL_HANDLE)
	{
		SQLFreeHandle(SQL_HANDLE_ENV, env);
	}

	if (doExit)
	{
		exit(1);
	}
}

void sqlok(SQLHSTMT stmt, SQLRETURN retcode, char* message)
{
	SQLTCHAR errormsg[ERR_MSG_LEN], sqlstate[SQL_SQLSTATE_SIZE+1];
	SQLINTEGER nativeerror = 0;
	SQLSMALLINT errormsglen = 0;
	if (retcode != SQL_SUCCESS && retcode != SQL_SUCCESS_WITH_INFO && retcode != SQL_NO_DATA)
	{
		cout << message << endl;
		cout << "SQLRETURN code is " << retcode ;
		if (retcode == SQL_ERROR)
		{
			retcode = SQLGetDiagRec(SQL_HANDLE_STMT, stmt, 1, sqlstate, &nativeerror, errormsg, ERR_MSG_LEN, &errormsglen);

			if (retcode == SQL_SUCCESS || retcode == SQL_SUCCESS_WITH_INFO)
			{
				cout << " SqlState : ";
				TCOUT << sqlstate;
				cout << " Error Message :";
				TCOUT << errormsg;
				cout << endl ;
			}
		}
		exit(1);
	}
}
